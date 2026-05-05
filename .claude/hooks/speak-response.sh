#!/bin/bash
# Streaming TTS enqueue hook. Wired to BOTH Stop and PreToolUse:
#   - PreToolUse: fires before each tool runs; intermediate narration up to
#     this point gets enqueued and starts speaking while the tool executes.
#   - Stop: fires when the turn ends; enqueues the closing text.
#
# Tracks /tmp/simona-last-queued.ts so each invocation only enqueues text
# blocks newer than the marker (no double-speaking). The marker resets to the
# last user prompt timestamp at the start of each turn (handled by
# voice-control.sh).
#
# Mute (~/.simona-mute) and read-aloud (/tmp/simona-reading.flag) flags
# short-circuit before any work.

set -euo pipefail

[ -f "$HOME/.simona-mute" ] && exit 0
[ -f /tmp/simona-reading.flag ] && exit 0

input=$(cat)
transcript=$(printf '%s' "$input" | jq -r '.transcript_path // empty')
session_id=$(printf '%s' "$input" | jq -r '.session_id // empty')
[ -z "$transcript" ] && exit 0
[ ! -f "$transcript" ] && exit 0

# Only the claimed active session speaks. Default state (no claim) is silent
# across all sessions — user explicitly opts in via "speak here" in chat.
active=$(cat /tmp/simona-active-session.id 2>/dev/null || echo "")
[ -z "$active" ] && exit 0
[ "$session_id" != "$active" ] && exit 0

# Last real user prompt (string content; tool_results are also type=user)
last_user_ts=$(jq -r '
  select(.type == "user" and (.message.content | type) == "string") | .timestamp
' "$transcript" 2>/dev/null | tail -1)
[ -z "$last_user_ts" ] && exit 0

MARKER_FILE="/tmp/simona-last-queued.ts"
QUEUE_DIR="/tmp/simona-queue"
mkdir -p "$QUEUE_DIR"

# Read marker; if absent or older than the last user prompt (= new turn),
# reset to the user prompt timestamp.
marker=$(cat "$MARKER_FILE" 2>/dev/null || echo "")
if [ -z "$marker" ] || [ "$marker" \< "$last_user_ts" ]; then
  marker="$last_user_ts"
fi

# Brief flush wait — same race we hit before with closing text not yet flushed
sleep 0.25

# Pull text entries newer than marker, one per line, base64-encoded so newlines
# in the content don't break the line-per-entry contract.
entries=$(jq -r --arg ts "$marker" '
  select(.type == "assistant" and .timestamp > $ts and (.message.content // [] | any(.type == "text")))
  | .timestamp + " " + ([.message.content[]? | select(.type == "text") | .text] | join("\n\n") | @base64)
' "$transcript" 2>/dev/null || true)

[ -z "$entries" ] && exit 0

# Write each new text block to the queue as a sequence-numbered file.
# Use nanosecond timestamp + monotonic counter for stable ordering.
seq_base=$(date +%s%N)
i=0
latest_ts="$marker"
while IFS=' ' read -r ts b64; do
  [ -z "$ts" ] && continue
  text=$(printf '%s' "$b64" | base64 --decode 2>/dev/null || true)
  [ -z "$text" ] && continue
  printf '%s' "$text" > "$QUEUE_DIR/${seq_base}_${i}.txt"
  i=$((i + 1))
  latest_ts="$ts"
done <<< "$entries"

# Persist new marker
printf '%s' "$latest_ts" > "$MARKER_FILE"

# Spawn drainer if not already running
LOCK="/tmp/simona-drainer.pid"
spawn=true
if [ -f "$LOCK" ]; then
  pid=$(cat "$LOCK" 2>/dev/null || echo)
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    spawn=false
  fi
fi
if $spawn; then
  PROJECT_DIR="/Users/hiper2d/projects/simona-ai-computer-operator"
  ( cd "$PROJECT_DIR" && uv run python mcp/kokoro/drainer.py >/dev/null 2>&1 ) &
  disown
fi

exit 0
