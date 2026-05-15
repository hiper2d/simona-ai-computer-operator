"""
Simona long-loop scheduler — deterministic, runs outside Claude.

Mirrors marlow's scheduler architecture: reads task YAMLs from
daemon/tasks/, computes what's due via cron expressions, decomposes
tasks into queue items, picks next subtask by priority. Pure
scheduling logic — never invokes Claude.

CLI:
    scheduler.py pick                          → schedule + pick next
    scheduler.py complete <id> <status> [--result <text>]
    scheduler.py dry-run                       → show what would be picked
    scheduler.py status                        → human-readable queue dump
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from glob import glob
from pathlib import Path

import yaml
from croniter import croniter

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_GLOB = str(REPO_ROOT / "daemon" / "tasks" / "*.yaml")
QUEUE_PATH = REPO_ROOT / "tasks" / "queue.json"
LAST_SCHEDULED_PATH = REPO_ROOT / "tasks" / "last_scheduled.json"
COMPLETED_DIR = REPO_ROOT / "tasks" / "completed"

PRIORITY_ORDER = {"high": 0, "normal": 1, "low": 2}


@dataclass
class QueueItem:
    id: str
    parent_task: str
    handler: str
    context: dict
    status: str
    priority: str
    queued_at: str
    started_at: str | None = None
    checkpoint: dict | None = None
    result: str | None = None


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_queue() -> list[QueueItem]:
    if not QUEUE_PATH.exists():
        return []
    raw = json.loads(QUEUE_PATH.read_text())
    return [QueueItem(**item) for item in raw]


def save_queue(queue: list[QueueItem]) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(json.dumps([asdict(item) for item in queue], indent=2))


def load_last_scheduled() -> dict[str, str]:
    if not LAST_SCHEDULED_PATH.exists():
        return {}
    return json.loads(LAST_SCHEDULED_PATH.read_text())


def save_last_scheduled(state: dict[str, str]) -> None:
    LAST_SCHEDULED_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAST_SCHEDULED_PATH.write_text(json.dumps(state, indent=2))


def load_task_definitions() -> list[dict]:
    defs = []
    for path in sorted(glob(TASKS_GLOB)):
        with open(path) as f:
            data = yaml.safe_load(f)
            if not data:
                continue
            data["_source"] = path
            defs.append(data)
    return defs


def is_due(task: dict, last_scheduled: dict[str, str], now: datetime) -> bool:
    schedule = task.get("schedule")
    if not schedule:
        return False
    last_iso = last_scheduled.get(task["name"])
    if last_iso is None:
        return False  # First sight — defer to next scheduled fire.
    last = datetime.fromisoformat(last_iso.replace("Z", "+00:00"))
    next_fire = croniter(schedule, last).get_next(datetime)
    if next_fire.tzinfo is None:
        next_fire = next_fire.replace(tzinfo=timezone.utc)
    return now >= next_fire


def _dedup_key(handler: str, context: dict) -> tuple:
    return (handler, context.get("target"), context.get("kind"))


def _is_duplicate(item: QueueItem, queue: list[QueueItem]) -> bool:
    key = _dedup_key(item.handler, item.context)
    for existing in queue:
        if existing.status not in ("pending", "in_progress"):
            continue
        if _dedup_key(existing.handler, existing.context) == key:
            return True
    return False


def decompose(task: dict, now: datetime) -> list[QueueItem]:
    items = []
    subtasks = task.get("subtasks", [])
    priority = task.get("priority", "normal")
    timestamp = now.strftime("%Y%m%d_%H%M")
    for sub in subtasks:
        items.append(QueueItem(
            id=f"{sub['id']}_{timestamp}",
            parent_task=task["name"],
            handler=sub["handler"],
            context=sub.get("context", {}),
            status="pending",
            priority=sub.get("priority", priority),
            queued_at=iso(now),
        ))
    return items


def schedule_due_tasks(queue: list[QueueItem], now: datetime, commit: bool = True) -> list[QueueItem]:
    last_scheduled = load_last_scheduled()
    defs = load_task_definitions()
    for task in defs:
        if is_due(task, last_scheduled, now):
            new_items = decompose(task, now)
            for item in new_items:
                if _is_duplicate(item, queue):
                    continue
                queue.append(item)
            last_scheduled[task["name"]] = iso(now)
        elif task["name"] not in last_scheduled:
            last_scheduled[task["name"]] = iso(now)
    if commit:
        save_last_scheduled(last_scheduled)
    return queue


def pick_next(queue: list[QueueItem]) -> QueueItem | None:
    in_progress = [i for i in queue if i.status == "in_progress"]
    if in_progress:
        in_progress.sort(key=lambda i: i.queued_at)
        return in_progress[0]
    pending = [i for i in queue if i.status == "pending"]
    if not pending:
        return None
    pending.sort(key=lambda i: (PRIORITY_ORDER.get(i.priority, 1), i.queued_at))
    return pending[0]


# ─── commands ──────────────────────────────────────────────────────────────


def cmd_pick(args):
    now = now_utc()
    queue = load_queue()
    queue = schedule_due_tasks(queue, now)
    chosen = pick_next(queue)
    if chosen is None:
        save_queue(queue)
        print("nothing to do", file=sys.stderr)
        sys.exit(1)
    chosen.status = "in_progress"
    chosen.started_at = iso(now)
    save_queue(queue)
    print(json.dumps(asdict(chosen)))


def cmd_complete(args):
    queue = load_queue()
    item = next((i for i in queue if i.id == args.id), None)
    if item is None:
        print(f"unknown subtask id: {args.id}", file=sys.stderr)
        sys.exit(2)
    item.status = args.status
    if args.result:
        item.result = args.result
    if args.checkpoint:
        item.checkpoint = json.loads(args.checkpoint)
    if args.status in ("done", "failed"):
        date_dir = COMPLETED_DIR / now_utc().strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        (date_dir / f"{item.id}.json").write_text(json.dumps(asdict(item), indent=2))
        queue = [i for i in queue if i.id != args.id]
    save_queue(queue)
    print(f"marked {args.id} as {args.status}")


def cmd_dry_run(args):
    now = now_utc()
    queue = load_queue()
    queue = schedule_due_tasks(queue, now, commit=False)
    chosen = pick_next(queue)
    print(f"queue size: {len(queue)}")
    if chosen:
        print(f"would pick: {chosen.id} ({chosen.handler}, priority={chosen.priority})")
    else:
        print("nothing pending")


def cmd_status(args):
    queue = load_queue()
    if not queue:
        print("queue is empty")
        return
    for item in queue:
        print(f"  [{item.status}] [{item.priority}] {item.id} ({item.handler})")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pick", help="Schedule due tasks and pick next subtask")
    p_complete = sub.add_parser("complete", help="Record a subtask outcome")
    p_complete.add_argument("id")
    p_complete.add_argument("status", choices=["done", "in_progress", "failed"])
    p_complete.add_argument("--checkpoint")
    p_complete.add_argument("--result")
    sub.add_parser("dry-run", help="Show what would be picked without state changes")
    sub.add_parser("status", help="Print the current queue")

    args = parser.parse_args()
    if args.cmd == "pick":
        cmd_pick(args)
    elif args.cmd == "complete":
        cmd_complete(args)
    elif args.cmd == "dry-run":
        cmd_dry_run(args)
    elif args.cmd == "status":
        cmd_status(args)


if __name__ == "__main__":
    main()
