"""
cost — per-tick cost telemetry for Simona's long-loop daemon.

`claude -p --output-format stream-json --verbose` emits JSONL events,
the last of which is a `result` event carrying `total_cost_usd` and
per-model `modelUsage`. This module consumes that stream from stdin,
extracts the final result, and appends a record to a JSONL cost log
at ~/.simona-loop/cost-log.jsonl.

Why this matters: starting 2026-06-15, Agent SDK / `claude -p` usage
moves from Max-5x subscription to a $100/month API-priced credit
(combined across all programmatic sessions — Marlow's and Simona's
draw from the same pool). We need to know our actual burn before
that switch flips.

Mirror of ~/projects/marlow/tools/cost.py. Keep the two in sync — if
you fix something here, mirror it there.

CLI:
    log --tick-id <id> --handler <name>
        Read stream-json from stdin, append cost record.
    extract-text
        Read stream-json from stdin, write assistant text to stdout.
    report [--period today|yesterday|mtd|all] [--handler <name>]
        Summarize spend.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path.home() / ".simona-loop"
COST_LOG = LOG_DIR / "cost-log.jsonl"

MONTHLY_CAP_USD = 100.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_stream(lines) -> dict | None:
    last_result = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "result":
            last_result = ev
    return last_result


def cmd_log(args):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    result = _parse_stream(sys.stdin)
    if result is None:
        record = {
            "ts": _now_iso(),
            "tick_id": args.tick_id,
            "handler": args.handler,
            "cost_usd": 0.0,
            "status": "no-result",
            "duration_ms": None,
            "model_usage": {},
        }
    else:
        usage = result.get("usage", {}) or {}
        model_usage = result.get("modelUsage", {}) or {}
        record = {
            "ts": _now_iso(),
            "tick_id": args.tick_id,
            "handler": args.handler,
            "cost_usd": float(result.get("total_cost_usd") or 0.0),
            "status": "error" if result.get("is_error") else "ok",
            "duration_ms": result.get("duration_ms"),
            "duration_api_ms": result.get("duration_api_ms"),
            "num_turns": result.get("num_turns"),
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
            "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
            "model_usage": {
                name: {
                    "cost_usd": float(v.get("costUSD") or 0.0),
                    "input_tokens": v.get("inputTokens", 0),
                    "output_tokens": v.get("outputTokens", 0),
                    "cache_read_input_tokens": v.get("cacheReadInputTokens", 0),
                    "cache_creation_input_tokens": v.get("cacheCreationInputTokens", 0),
                }
                for name, v in model_usage.items()
            },
        }
    with COST_LOG.open("a") as f:
        f.write(json.dumps(record) + "\n")


def cmd_extract_text(args):
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "assistant":
            msg = ev.get("message", {})
            for block in msg.get("content", []) or []:
                if block.get("type") == "text":
                    text = block.get("text", "")
                    if text:
                        print(text)


def _load_records() -> list[dict]:
    if not COST_LOG.exists():
        return []
    out = []
    for line in COST_LOG.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _filter(records: list[dict], period: str) -> list[dict]:
    now = datetime.now(timezone.utc)
    if period == "all":
        return records

    def _ts(rec):
        return datetime.fromisoformat(rec["ts"].replace("Z", "+00:00"))

    if period == "today":
        return [r for r in records if _ts(r).date() == now.date()]
    if period == "yesterday":
        from datetime import timedelta
        y = (now - timedelta(days=1)).date()
        return [r for r in records if _ts(r).date() == y]
    if period == "mtd":
        return [r for r in records if _ts(r).year == now.year and _ts(r).month == now.month]
    raise ValueError(f"unknown period: {period}")


def cmd_report(args):
    records = _load_records()
    if args.handler:
        records = [r for r in records if r.get("handler") == args.handler]
    if not records:
        print(f"No cost records yet at {COST_LOG}.")
        return

    period_records = _filter(records, args.period)
    total = sum(r["cost_usd"] for r in period_records)
    n = len(period_records)

    print(f"Cost report ({args.period}) — Simona daemon")
    print(f"  Records: {n}")
    print(f"  Total:   ${total:.4f}")
    if n > 0:
        avg = total / n
        print(f"  Avg/tick: ${avg:.4f}")

    if args.period == "mtd":
        now = datetime.now(timezone.utc)
        day_of_month = now.day
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
        days_in_month = (next_month - now.replace(day=1)).days
        if day_of_month > 0:
            projection = total / day_of_month * days_in_month
            print(f"  Day:     {day_of_month}/{days_in_month}")
            print(f"  Projected month-end: ${projection:.2f}")
            print(f"  (Simona-only — combine with Marlow for total against $100 cap)")

    by_handler: dict[str, list[float]] = defaultdict(list)
    for r in period_records:
        by_handler[r.get("handler") or "unknown"].append(r["cost_usd"])
    if by_handler:
        print()
        print("By handler:")
        ranked = sorted(by_handler.items(), key=lambda kv: -sum(kv[1]))
        for name, costs in ranked:
            print(f"  {name:32s}  ${sum(costs):8.4f}  ({len(costs)} runs, avg ${sum(costs)/len(costs):.4f})")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_log = sub.add_parser("log", help="Parse stream-json from stdin, append cost record")
    p_log.add_argument("--tick-id", required=True)
    p_log.add_argument("--handler", required=True)

    sub.add_parser("extract-text", help="Extract human-readable text from stream-json stdin")

    p_report = sub.add_parser("report", help="Summarize spend")
    p_report.add_argument("--period", choices=["today", "yesterday", "mtd", "all"], default="mtd")
    p_report.add_argument("--handler", help="Filter to one handler")

    args = parser.parse_args()
    if args.cmd == "log":
        cmd_log(args)
    elif args.cmd == "extract-text":
        cmd_extract_text(args)
    elif args.cmd == "report":
        cmd_report(args)


if __name__ == "__main__":
    main()
