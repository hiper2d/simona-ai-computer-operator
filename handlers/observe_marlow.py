"""
observe_marlow — orchestration for Simona's daily Marlow observation tick.

Surfaces everything Simona needs to see how Marlow's state is evolving:
working memory, recent tick logs, threads (with mtime so changes are
visible), latest news digests, draft counts, and queue health. Simona's
session reads this snapshot, compares it against yesterday's
observation file, and writes a new observation to
memory/observations/marlow/<date>.md.

CLI:
    python handlers/observe_marlow.py snapshot
        → JSON snapshot of Marlow's current state
    python handlers/observe_marlow.py last-observation
        → path + body of yesterday's observation (or null)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SIMONA_OBS_DIR = REPO_ROOT / "memory" / "observations" / "marlow"

MARLOW_ROOT = Path.home() / "projects" / "marlow"
MARLOW_WORKING = MARLOW_ROOT / "memory" / "working.md"
MARLOW_RECENT = MARLOW_ROOT / "memory" / "recent"
MARLOW_THREADS = MARLOW_ROOT / "projects" / "research" / "threads"
MARLOW_NOTES = MARLOW_ROOT / "projects" / "research" / "notes"
MARLOW_NEWS = MARLOW_ROOT / "digests" / "news"
MARLOW_DRAFTS = MARLOW_ROOT / "projects" / "blog" / "drafts"
MARLOW_QUEUE = MARLOW_ROOT / "tasks" / "queue.json"


def _read(path: Path) -> str:
    try:
        return path.read_text()
    except OSError:
        return ""


def _mtime_iso(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return None


def _list_dir(path: Path, pattern: str = "*.md", limit: int | None = None) -> list[dict]:
    if not path.exists():
        return []
    files = sorted(path.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    if limit:
        files = files[:limit]
    return [
        {"name": f.name, "size": f.stat().st_size, "mtime": _mtime_iso(f)}
        for f in files
        if f.name != ".gitkeep"
    ]


def snapshot() -> dict:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=2)

    # Working memory — full content (it's capped at ~10KB).
    working_md = _read(MARLOW_WORKING)

    # Threads — full content of each (file is the running editorial commentary).
    threads = []
    if MARLOW_THREADS.exists():
        for f in sorted(MARLOW_THREADS.glob("*.md")):
            if f.name == ".gitkeep":
                continue
            threads.append({
                "slug": f.stem,
                "size": f.stat().st_size,
                "mtime": _mtime_iso(f),
                "body": _read(f),
            })

    # Recent ticks within the last 2 days (file content; these are short).
    recent_ticks = []
    if MARLOW_RECENT.exists():
        for f in sorted(MARLOW_RECENT.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True):
            if f.name == ".gitkeep":
                continue
            mtime_ts = f.stat().st_mtime
            if datetime.fromtimestamp(mtime_ts, tz=timezone.utc) < cutoff:
                break
            recent_ticks.append({
                "name": f.name,
                "size": f.stat().st_size,
                "mtime": _mtime_iso(f),
                "body": _read(f),
            })

    # Latest news digest (just metadata + body of yesterday's).
    latest_news = None
    if MARLOW_NEWS.exists():
        files = sorted(MARLOW_NEWS.glob("*.md"), reverse=True)
        if files:
            f = files[0]
            latest_news = {
                "name": f.name,
                "size": f.stat().st_size,
                "mtime": _mtime_iso(f),
                "body": _read(f),
            }

    # Drafts inventory (size and review state).
    drafts = []
    if MARLOW_DRAFTS.exists():
        for f in sorted(MARLOW_DRAFTS.glob("*.md")):
            if f.name == ".gitkeep" or f.name.endswith(".simona-review.md"):
                continue
            slug = f.stem
            review = MARLOW_DRAFTS / f"{slug}.simona-review.md"
            drafts.append({
                "slug": slug,
                "size": f.stat().st_size,
                "mtime": _mtime_iso(f),
                "has_simona_review": review.exists(),
            })

    # Queue health.
    queue_summary = {"pending": 0, "in_progress": 0, "total": 0}
    if MARLOW_QUEUE.exists():
        try:
            items = json.loads(_read(MARLOW_QUEUE))
            queue_summary["total"] = len(items)
            queue_summary["pending"] = sum(1 for i in items if i.get("status") == "pending")
            queue_summary["in_progress"] = sum(1 for i in items if i.get("status") == "in_progress")
        except json.JSONDecodeError:
            pass

    return {
        "captured_at": now.isoformat(),
        "marlow_root": str(MARLOW_ROOT),
        "working_md": {
            "size": len(working_md),
            "mtime": _mtime_iso(MARLOW_WORKING),
            "body": working_md,
        },
        "threads": threads,
        "recent_ticks_2d": recent_ticks,
        "latest_news_digest": latest_news,
        "drafts": drafts,
        "queue": queue_summary,
        "observation_dir": str(SIMONA_OBS_DIR),
    }


def last_observation() -> dict:
    """Return path + body of the most recent observation, if any."""
    if not SIMONA_OBS_DIR.exists():
        return {"path": None, "body": None}
    files = sorted(SIMONA_OBS_DIR.glob("*.md"), reverse=True)
    if not files:
        return {"path": None, "body": None}
    f = files[0]
    return {"path": str(f), "mtime": _mtime_iso(f), "body": _read(f)}


def cmd_snapshot(args):
    print(json.dumps(snapshot(), indent=2, ensure_ascii=False))


def cmd_last(args):
    print(json.dumps(last_observation(), indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("snapshot", help="Snapshot Marlow's current state as JSON")
    sub.add_parser("last-observation", help="Get the most recent observation file")
    args = parser.parse_args()
    if args.cmd == "snapshot":
        cmd_snapshot(args)
    elif args.cmd == "last-observation":
        cmd_last(args)


if __name__ == "__main__":
    main()
