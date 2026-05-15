#!/bin/bash
# Simona long-loop tick. LaunchAgent entry point. Runs every 2 hours
# while the system is awake.
#
# Flow:
#   1. Killswitch check (~/.simona-loop/stop)
#   2. Pause check (~/.simona-loop/pause)
#   3. Acquire lock (/tmp/simona-loop.lock)
#   4. Pick next subtask via daemon/scheduler.py
#   5. Invoke Claude Code session (Simona) to execute the named handler
#   6. Record outcome
#   7. Release lock

set -euo pipefail

# Cron-style stripped env — add common bin dirs so `claude` and `uv` resolve.
export PATH="$HOME/.local/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SIMONA_DIR="$HOME/.simona-loop"
KILLSWITCH="$SIMONA_DIR/stop"
PAUSE="$SIMONA_DIR/pause"
SESSIONS_LOG="$SIMONA_DIR/sessions.log"
LOCK_FILE="/tmp/simona-loop.lock"
SUBTASK_FILE="/tmp/simona-loop-subtask.json"
RESULT_FILE="/tmp/simona-loop-result.json"
TICK_TIMEOUT_SEC=420   # 7 min — reviews can be longer than marlow's ticks

mkdir -p "$SIMONA_DIR"

# Telegram creds come from marlow's .env so Simona shares the same bot.
MARLOW_ENV="$HOME/projects/marlow/.env"
if [ -f "$MARLOW_ENV" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$MARLOW_ENV"
    set +a
fi

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

run_with_timeout() {
    local seconds=$1; shift
    if command -v timeout >/dev/null 2>&1; then
        timeout "$seconds" "$@"
    elif command -v gtimeout >/dev/null 2>&1; then
        gtimeout "$seconds" "$@"
    else
        perl -e 'use POSIX qw(SIGTERM); my $pid = fork; if ($pid == 0) { exec @ARGV[1..$#ARGV] or exit 127; } eval { local $SIG{ALRM} = sub { kill SIGTERM, $pid; die "timeout\n"; }; alarm $ARGV[0]; waitpid $pid, 0; alarm 0; }; exit ($@ eq "timeout\n" ? 124 : ($? >> 8));' "$seconds" "$@"
    fi
}

cleanup() {
    rm -f "$LOCK_FILE" "$SUBTASK_FILE" "$RESULT_FILE"
}
trap cleanup EXIT

if [ -f "$KILLSWITCH" ]; then
    log "killswitch present, exiting"
    exit 0
fi

if [ -f "$PAUSE" ]; then
    log "paused, skipping tick"
    exit 0
fi

if [ -f "$LOCK_FILE" ]; then
    log "previous tick still running (lock held), exiting"
    exit 0
fi
echo $$ > "$LOCK_FILE"

cd "$REPO_ROOT"
SUBTASK_JSON=$(uv run python daemon/scheduler.py pick 2>&1) || {
    rc=$?
    if [ $rc -eq 1 ]; then
        log "nothing to do"
        exit 0
    fi
    log "scheduler error (exit $rc): $SUBTASK_JSON"
    exit $rc
}

SUBTASK_ID=$(echo "$SUBTASK_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
SUBTASK_HANDLER=$(echo "$SUBTASK_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['handler'])")
log "picked subtask: $SUBTASK_ID (handler: $SUBTASK_HANDLER)"

echo "$SUBTASK_JSON" > "$SUBTASK_FILE"
rm -f "$RESULT_FILE"

# Invoke Claude Code (Simona's session). cwd is repo root → CLAUDE.md
# + SOUL.md load automatically. The session knows it's running in
# long-loop mode rather than interactive mode from the prompt.
PROMPT="You are Simona running as a long-loop daemon tick rather than an interactive session with Alex. A subtask is queued for you at $SUBTASK_FILE — read it, execute the named handler per the contract in daemon/PROTOCOL.md, write your outcome JSON to $RESULT_FILE before exiting. Do not chat. Do not narrate. Just do the work and exit."

if run_with_timeout "$TICK_TIMEOUT_SEC" claude -p "$PROMPT" >> "$SESSIONS_LOG" 2>&1; then
    log "session exited cleanly"
else
    rc=$?
    log "session exited with code $rc (124 = timeout)"
fi

if [ ! -f "$RESULT_FILE" ]; then
    log "WARNING: session did not write a result file — marking subtask failed"
    cat > "$RESULT_FILE" <<EOF
{"status": "failed", "result": "session exited without writing result file", "checkpoint": null, "notify": null}
EOF
fi

RESULT_STATUS=$(python3 -c "import json; print(json.load(open('$RESULT_FILE'))['status'])")
RESULT_TEXT=$(python3 -c "import json; print(json.load(open('$RESULT_FILE'))['result'])")
RESULT_NOTIFY=$(python3 -c "import json; r=json.load(open('$RESULT_FILE')); print(json.dumps(r.get('notify')) if r.get('notify') else '')")

uv run python daemon/scheduler.py complete "$SUBTASK_ID" "$RESULT_STATUS" --result "$RESULT_TEXT"

if [ -n "$RESULT_NOTIFY" ]; then
    NOTIFY_MSG=$(echo "$RESULT_NOTIFY" | python3 -c "import json,sys; print(json.load(sys.stdin)['message'])")
    uv run python daemon/notify.py "$NOTIFY_MSG" || true
fi

log "tick complete"
