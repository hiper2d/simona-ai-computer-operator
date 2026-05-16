"""
review_drafts — orchestration handler for Simona's draft review loop.

A draft needs review when its current `<slug>.md` is newer than its
`<slug>.simona-review.md` (or no review sibling exists). That covers
both first-time drafts and v2+ revisions Marlow has just written.

Reviews terminate or continue the iteration loop:
- verdicts `ship-as-is` / `reject` → terminal (notify Alex)
- verdicts `minor-edits` / `major-revisions` → queue a `revise_draft`
  subtask in Marlow's queue and stay silent, unless we've already
  hit the 3-version cap (then terminate, notify Alex)

CLI:
    list-pending
        JSON: {marlow_root, count, items: [{slug, draft_path, ...,
        version, prior_review_path, prior_review_verdict}]}
    find --slug <slug>
        JSON: same shape as one list-pending item.
    queue-revise --slug <slug>
        Append a high-priority `revise_draft` subtask to Marlow's queue.
        Used after writing a continuing review. No-op + exit 1 if a
        revise for this slug is already pending/in-progress.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MARLOW_ROOT = Path.home() / "projects" / "marlow"
DRAFTS_DIR = MARLOW_ROOT / "projects" / "blog" / "drafts"
VERSIONS_DIR = DRAFTS_DIR / "versions"
MARLOW_QUEUE = MARLOW_ROOT / "tasks" / "queue.json"
MARLOW_COMPLETED = MARLOW_ROOT / "tasks" / "completed"

MAX_VERSIONS = 3
STUCK_LOOKBACK_DAYS = 3        # how far back to scan for failed revises
MAX_REVISE_RETRIES = 1          # auto-retry once, then escalate


def _parse_verdict(review_path: Path) -> str | None:
    if not review_path.exists():
        return None
    text = review_path.read_text()
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    for line in text[3:end].splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        if k.strip() == "verdict":
            return v.strip().strip('"').strip("'")
    return None


def _version_count(slug: str) -> int:
    """Current version number of the draft. 1 = original, 2/3 = revisions."""
    archive = VERSIONS_DIR / slug
    if not archive.exists():
        return 1
    return 1 + sum(1 for f in archive.glob("v*.md"))


def _describe(slug: str, draft_path: Path) -> dict:
    review_path = DRAFTS_DIR / f"{slug}.simona-review.md"
    return {
        "slug": slug,
        "draft_path": str(draft_path),
        "review_path": str(review_path),
        "size": draft_path.stat().st_size if draft_path.exists() else 0,
        "version": _version_count(slug),
        "prior_review_exists": review_path.exists(),
        "prior_review_verdict": _parse_verdict(review_path),
    }


def list_pending() -> list[dict]:
    """Drafts where the current file is newer than its review (or no review yet)."""
    if not DRAFTS_DIR.exists():
        return []
    items = []
    for f in sorted(DRAFTS_DIR.glob("*.md")):
        if f.name.endswith(".simona-review.md") or f.name.startswith("."):
            continue
        slug = f.stem
        review_path = DRAFTS_DIR / f"{slug}.simona-review.md"
        if review_path.exists() and review_path.stat().st_mtime >= f.stat().st_mtime:
            # Review is current — already covered this version.
            continue
        items.append(_describe(slug, f))
    return items


def find_by_slug(slug: str) -> dict:
    draft_path = DRAFTS_DIR / f"{slug}.md"
    item = _describe(slug, draft_path)
    item["found"] = draft_path.exists()
    return item


def queue_revise(slug: str) -> dict:
    """Append a `revise_draft` subtask to Marlow's queue.

    Concurrency: this is read-modify-write on a file Marlow's scheduler
    also touches. Race window is small (both schedulers run minutes
    apart, both are idempotent on their own work) but a clash here
    means one queue mutation is lost. If we hit this in practice,
    add fcntl-based locking. Documenting as known risk.
    """
    if not MARLOW_QUEUE.exists():
        queue: list[dict] = []
    else:
        queue = json.loads(MARLOW_QUEUE.read_text())

    # Skip if a revise for this slug is already pending/in-progress.
    for item in queue:
        if item.get("handler") == "revise_draft" \
           and item.get("context", {}).get("slug") == slug \
           and item.get("status") in ("pending", "in_progress"):
            return {"queued": False, "reason": "already-pending", "existing_id": item["id"]}

    now = datetime.now(timezone.utc).replace(microsecond=0)
    iso = now.isoformat().replace("+00:00", "Z")
    new_item = {
        "id": f"revise_{slug}_{now.strftime('%Y%m%d_%H%M')}",
        "parent_task": "simona_queued_revise",
        "project": "blog",
        "handler": "revise_draft",
        "context": {"slug": slug},
        "status": "pending",
        "priority": "high",
        "queued_at": iso,
        "started_at": None,
        "checkpoint": None,
        "result": None,
    }
    queue.append(new_item)
    MARLOW_QUEUE.write_text(json.dumps(queue, indent=2))
    return {"queued": True, "id": new_item["id"]}


def _load_marlow_queue() -> list[dict]:
    if not MARLOW_QUEUE.exists():
        return []
    return json.loads(MARLOW_QUEUE.read_text())


def _revise_active_for_slug(slug: str) -> bool:
    """True if Marlow's queue already has a pending/in-progress revise for this slug."""
    for item in _load_marlow_queue():
        if item.get("handler") == "revise_draft" \
           and item.get("context", {}).get("slug") == slug \
           and item.get("status") in ("pending", "in_progress"):
            return True
    return False


def _failed_revises(lookback_days: int = STUCK_LOOKBACK_DAYS) -> dict[str, list[dict]]:
    """Scan Marlow's completed/ for failed revise_draft tasks, grouped by slug.

    Returns {slug: [completion_record, ...]} for the lookback window.
    """
    out: dict[str, list[dict]] = {}
    if not MARLOW_COMPLETED.exists():
        return out
    today = datetime.now(timezone.utc).date()
    for day_offset in range(lookback_days + 1):
        date_dir = MARLOW_COMPLETED / (today - timedelta(days=day_offset)).isoformat()
        if not date_dir.exists():
            continue
        for f in date_dir.glob("*.json"):
            try:
                rec = json.loads(f.read_text())
            except json.JSONDecodeError:
                continue
            if rec.get("handler") != "revise_draft":
                continue
            if rec.get("status") != "failed":
                continue
            slug = rec.get("context", {}).get("slug")
            if not slug:
                continue
            out.setdefault(slug, []).append(rec)
    return out


def check_stuck() -> list[dict]:
    """Identify stuck revision loops; classify each slug as requeue or escalate.

    A slug needs attention if its most recent revise_draft completion was a
    failure AND there's no pending/in-progress retry already queued.

    Action:
      - failed once  → requeue (transient — server overloads, etc.)
      - failed twice → escalate (likely a real bug, surface to Alex)
    """
    failed = _failed_revises()
    actions = []
    for slug, recs in failed.items():
        if _revise_active_for_slug(slug):
            continue  # Already retrying
        n = len(recs)
        recs.sort(key=lambda r: r.get("started_at") or r.get("queued_at") or "")
        last = recs[-1]
        actions.append({
            "slug": slug,
            "action": "requeue" if n <= MAX_REVISE_RETRIES else "escalate",
            "failure_count": n,
            "last_failed_id": last.get("id"),
            "last_failed_at": last.get("started_at"),
            "last_failure_reason": last.get("result"),
        })
    return actions


def cmd_check_stuck(args):
    actions = check_stuck()
    print(json.dumps({"count": len(actions), "actions": actions}, indent=2, ensure_ascii=False))


def cmd_list_pending(args):
    items = list_pending()
    out = {
        "marlow_root": str(MARLOW_ROOT),
        "drafts_dir": str(DRAFTS_DIR),
        "count": len(items),
        "items": items,
        "max_versions": MAX_VERSIONS,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))


def cmd_find(args):
    result = find_by_slug(args.slug)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["found"] else 1)


def cmd_queue_revise(args):
    result = queue_revise(args.slug)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("queued") else 1)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list-pending", help="List drafts whose current version is unreviewed")
    p_find = sub.add_parser("find", help="Look up a specific draft by slug")
    p_find.add_argument("--slug", required=True)
    p_queue = sub.add_parser("queue-revise", help="Append a revise_draft subtask to Marlow's queue")
    p_queue.add_argument("--slug", required=True)
    sub.add_parser("check-stuck", help="Find stuck revision loops; classify as requeue or escalate")
    args = parser.parse_args()
    if args.cmd == "list-pending":
        cmd_list_pending(args)
    elif args.cmd == "find":
        cmd_find(args)
    elif args.cmd == "queue-revise":
        cmd_queue_revise(args)
    elif args.cmd == "check-stuck":
        cmd_check_stuck(args)


if __name__ == "__main__":
    main()
