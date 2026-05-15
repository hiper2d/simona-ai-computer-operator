#!/usr/bin/env python3
"""Simona control CLI — voice/playback plus the long-loop agent.

Voice/playback (existing):
    simona mute        Persistent global mute (touches ~/.simona-mute, kills audio).
    simona unmute      Lift global mute.
    simona stop        Kill in-flight playback.
    simona pause       Pause current playback (SIGSTOP drainer + afplay).
    simona continue    Resume paused playback (SIGCONT). Alias: resume.
    simona replay      Replay the last spoken text.
    simona status      Show voice/playback state.

Long-loop agent (the Simona daemon that reviews Marlow's drafts and
monitors her state — separate LaunchAgent from the voice system, state
files in ~/.simona-loop/ not ~/.simona-mute):
    simona agent install      Install launchd agent (turn loop on).
    simona agent uninstall    Remove launchd agent (turn loop off).
    simona agent tick         Fire one tick now (manual).
    simona agent status       Print queue + recent ticks.
    simona agent pause        Touch ~/.simona-loop/stop (loop pauses).
    simona agent resume       Clear killswitch / pause flags.
    simona agent logs [-n N] [-f]   Tail ~/.simona-loop/log.
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOME = Path.home()

MUTE_FLAG     = HOME / ".simona-mute"
PAUSE_FLAG    = Path("/tmp/simona-paused.flag")
QUEUE_DIR     = Path("/tmp/simona-queue")
DRAINER_PID   = Path("/tmp/simona-drainer.pid")
LAST_TS       = Path("/tmp/simona-last-queued.ts")
ACTIVE_FILE   = Path("/tmp/simona-active-session.id")
CURRENT_TEXT  = Path("/tmp/simona-current-text.txt")
PREV_TEXT     = Path("/tmp/simona-prev-text.txt")

# Long-loop agent state — separate namespace from voice/playback.
SIMONA_LOOP_DIR = HOME / ".simona-loop"
LOOP_KILLSWITCH = SIMONA_LOOP_DIR / "stop"
LOOP_PAUSE      = SIMONA_LOOP_DIR / "pause"
LOOP_LOG        = SIMONA_LOOP_DIR / "log"
DAEMON_DIR      = REPO_ROOT / "daemon"


def _pgrep_f(pattern: str) -> list[int]:
    try:
        out = subprocess.check_output(
            ["pgrep", "-f", pattern], text=True, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        return []
    return [int(p) for p in out.split() if p]


def _pgrep_x(name: str) -> list[int]:
    try:
        out = subprocess.check_output(
            ["pgrep", "-x", name], text=True, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        return []
    return [int(p) for p in out.split() if p]


def _audio_pids() -> list[int]:
    return (
        _pgrep_f("mcp/kokoro/drainer.py")
        + _pgrep_f("mcp/kokoro/cli.py")
        + _pgrep_x("afplay")
    )


def _kill_audio() -> None:
    for pid in _audio_pids():
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if QUEUE_DIR.exists():
        shutil.rmtree(QUEUE_DIR, ignore_errors=True)
    for f in (DRAINER_PID, LAST_TS, PAUSE_FLAG):
        try:
            f.unlink()
        except FileNotFoundError:
            pass


def _signal_audio(sig: int) -> int:
    pids = _pgrep_f("mcp/kokoro/drainer.py") + _pgrep_x("afplay")
    sent = 0
    for pid in pids:
        try:
            os.kill(pid, sig)
            sent += 1
        except ProcessLookupError:
            pass
    return sent


def cmd_mute(_args) -> None:
    MUTE_FLAG.touch()
    _kill_audio()
    print("muted globally — 'simona unmute' to lift")


def cmd_unmute(_args) -> None:
    try:
        MUTE_FLAG.unlink()
    except FileNotFoundError:
        pass
    print("unmuted (claim is independent — say 'speak here' to claim a session)")


def cmd_stop(_args) -> None:
    _kill_audio()
    print("stopped current playback")


def cmd_pause(_args) -> None:
    n = _signal_audio(signal.SIGSTOP)
    if n == 0:
        print("nothing playing to pause")
        return
    PAUSE_FLAG.touch()
    print(f"paused ({n} proc) — 'simona continue' to resume")


def cmd_continue(_args) -> None:
    paused = PAUSE_FLAG.exists()
    n = _signal_audio(signal.SIGCONT)
    try:
        PAUSE_FLAG.unlink()
    except FileNotFoundError:
        pass
    if n == 0 and not paused:
        print("nothing paused")
        return
    print(f"resumed ({n} proc)")


def cmd_replay(_args) -> None:
    text = ""
    for p in (CURRENT_TEXT, PREV_TEXT):
        if p.exists():
            t = p.read_text().strip()
            if t:
                text = t
                break
    if not text:
        print("nothing to replay")
        return

    _kill_audio()
    QUEUE_DIR.mkdir(exist_ok=True)
    seq = int(time.time() * 1e9)
    (QUEUE_DIR / f"{seq}_replay.txt").write_text(text)

    subprocess.Popen(
        ["uv", "run", "python", "mcp/kokoro/drainer.py"],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    print(f"replaying ({len(text)} chars)")


def cmd_status(_args) -> None:
    muted   = MUTE_FLAG.exists()
    paused  = PAUSE_FLAG.exists()
    drainer = bool(_pgrep_f("mcp/kokoro/drainer.py"))
    afplay  = bool(_pgrep_x("afplay"))
    active  = ACTIVE_FILE.read_text().strip() if ACTIVE_FILE.exists() else ""

    cur_chars  = len(CURRENT_TEXT.read_text()) if CURRENT_TEXT.exists() else 0
    prev_chars = len(PREV_TEXT.read_text())    if PREV_TEXT.exists()    else 0

    print(f"muted:      {'yes' if muted else 'no'}")
    print(f"paused:     {'yes' if paused else 'no'}")
    print(f"playing:    {'yes' if afplay else 'no'} (drainer: {'up' if drainer else 'down'})")
    print(f"active:     {active or '(none — silent everywhere)'}")
    print(f"replay buf: current={cur_chars}ch prev={prev_chars}ch")


# ─── long-loop agent subcommands ──────────────────────────────────────────


def _run_in_repo(*cmd: str) -> int:
    return subprocess.call(list(cmd), cwd=str(REPO_ROOT))


def cmd_agent_install(_args) -> None:
    sys.exit(_run_in_repo("bash", str(DAEMON_DIR / "install-agent.sh")))


def cmd_agent_uninstall(_args) -> None:
    sys.exit(_run_in_repo("bash", str(DAEMON_DIR / "uninstall-agent.sh")))


def cmd_agent_tick(_args) -> None:
    sys.exit(_run_in_repo("bash", str(DAEMON_DIR / "tick.sh")))


def cmd_agent_status(_args) -> None:
    sys.exit(_run_in_repo("uv", "run", "python", "daemon/scheduler.py", "status"))


def cmd_agent_pause(_args) -> None:
    SIMONA_LOOP_DIR.mkdir(parents=True, exist_ok=True)
    LOOP_KILLSWITCH.touch()
    print(f"paused — {LOOP_KILLSWITCH} created")
    print("agent will still fire every 2h, but each tick will exit clean.")
    print("resume with: simona agent resume")


def cmd_agent_resume(_args) -> None:
    removed = []
    for flag in (LOOP_KILLSWITCH, LOOP_PAUSE):
        if flag.exists():
            flag.unlink()
            removed.append(str(flag))
    if removed:
        print("resumed — removed:")
        for r in removed:
            print(f"  {r}")
    else:
        print("not paused — no killswitch or pause flag was set")


def cmd_agent_logs(args) -> None:
    if not LOOP_LOG.exists():
        print(f"{LOOP_LOG} does not exist yet — agent has not run.")
        sys.exit(1)
    if args.follow:
        os.execvp("tail", ["tail", "-n", str(args.lines), "-f", str(LOOP_LOG)])
    else:
        os.execvp("tail", ["tail", "-n", str(args.lines), str(LOOP_LOG)])


# ─── on-demand subtask injection ──────────────────────────────────────────


def _queue_subtask(handler: str, parent_task: str, context: dict, id_suffix: str) -> None:
    """Inject a high-priority subtask into the long-loop queue.

    Writes directly to tasks/queue.json with no daemon imports — keeps
    this CLI pure-stdlib like the rest of it. Queue shape must match
    daemon/scheduler.py's QueueItem dataclass.
    """
    import json
    from datetime import datetime, timezone

    queue_path = REPO_ROOT / "tasks" / "queue.json"
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    now_iso = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    queue: list = json.loads(queue_path.read_text()) if queue_path.exists() else []
    item = {
        "id": f"{id_suffix}_{now.strftime('%Y%m%d_%H%M')}",
        "parent_task": parent_task,
        "handler": handler,
        "context": context,
        "status": "pending",
        "priority": "high",
        "queued_at": now_iso,
        "started_at": None,
        "checkpoint": None,
        "result": None,
    }
    queue.append(item)
    queue_path.write_text(json.dumps(queue, indent=2))
    print(f"queued: {item['id']}")
    print("run `simona agent tick` to fire now, or wait for next agent tick (≤2h)")


def cmd_review_now(args) -> None:
    """Queue an on-demand review subtask, optionally for a specific draft slug."""
    if args.slug:
        ctx = {"slug": args.slug, "on_demand": True}
        suffix = f"review_{args.slug}"
    else:
        ctx = {"on_demand": True}
        suffix = "review_pending"
    _queue_subtask("review_drafts", "review_drafts_ondemand", ctx, suffix)


def cmd_observe_now(_args) -> None:
    """Queue an on-demand observe-Marlow subtask."""
    _queue_subtask("observe_marlow", "observe_marlow_ondemand", {"on_demand": True}, "observe")


def main() -> None:
    p = argparse.ArgumentParser(prog="simona", description="Simona control CLI")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("mute",     help="Persistent global mute").set_defaults(func=cmd_mute)
    sub.add_parser("unmute",   help="Lift global mute").set_defaults(func=cmd_unmute)
    sub.add_parser("stop",     help="Kill current playback").set_defaults(func=cmd_stop)
    sub.add_parser("pause",    help="Pause current playback (SIGSTOP)").set_defaults(func=cmd_pause)
    sub.add_parser("continue", help="Resume paused playback (SIGCONT)").set_defaults(func=cmd_continue)
    sub.add_parser("resume",   help="Alias for continue").set_defaults(func=cmd_continue)
    sub.add_parser("replay",   help="Replay last spoken text").set_defaults(func=cmd_replay)
    sub.add_parser("status",   help="Show voice/playback state").set_defaults(func=cmd_status)

    p_agent = sub.add_parser("agent", help="Long-loop agent (review/monitor Marlow)")
    agent_sub = p_agent.add_subparsers(dest="agent_cmd", required=True)
    agent_sub.add_parser("install",   help="Install launchd agent").set_defaults(func=cmd_agent_install)
    agent_sub.add_parser("uninstall", help="Remove launchd agent").set_defaults(func=cmd_agent_uninstall)
    agent_sub.add_parser("tick",      help="Fire one tick now").set_defaults(func=cmd_agent_tick)
    agent_sub.add_parser("status",    help="Show queue + scheduled tasks").set_defaults(func=cmd_agent_status)
    agent_sub.add_parser("pause",     help="Touch killswitch (loop pauses)").set_defaults(func=cmd_agent_pause)
    agent_sub.add_parser("resume",    help="Clear killswitch/pause flags").set_defaults(func=cmd_agent_resume)
    p_logs = agent_sub.add_parser("logs", help="Tail ~/.simona-loop/log")
    p_logs.add_argument("-n", "--lines", type=int, default=50)
    p_logs.add_argument("-f", "--follow", action="store_true")
    p_logs.set_defaults(func=cmd_agent_logs)

    p_review = sub.add_parser("review", help="Queue an on-demand draft review (optional: specific slug)")
    p_review.add_argument("slug", nargs="?", help="Marlow draft slug; omit to review all pending")
    p_review.set_defaults(func=cmd_review_now)

    p_observe = sub.add_parser("observe", help="Queue an on-demand Marlow observation tick")
    p_observe.set_defaults(func=cmd_observe_now)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
