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
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MARLOW_ROOT = Path.home() / "projects" / "marlow"
DRAFTS_DIR = MARLOW_ROOT / "projects" / "blog" / "drafts"
VERSIONS_DIR = DRAFTS_DIR / "versions"
MARLOW_QUEUE = MARLOW_ROOT / "tasks" / "queue.json"

MAX_VERSIONS = 3


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
    args = parser.parse_args()
    if args.cmd == "list-pending":
        cmd_list_pending(args)
    elif args.cmd == "find":
        cmd_find(args)
    elif args.cmd == "queue-revise":
        cmd_queue_revise(args)


if __name__ == "__main__":
    main()
