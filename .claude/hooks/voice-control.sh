#!/bin/bash
# UserPromptSubmit hook. Three jobs:
#   1) Intercept short voice-control commands (mute / unmute / shut up / etc.).
#   2) Manage the active speaking session: which Claude Code session, if any,
#      gets to speak. Default is "none" — sessions stay silent until claimed.
#   3) On a normal pass-through prompt, kill any in-flight audio if the active
#      speaker is THIS session (so a new turn cleanly interrupts its old one).
#
# Recognized phrases (case-insensitive, whole-prompt match after collapsing
# punctuation to spaces):
#
#   mute / shut up / shutup / be quiet / stay quiet / silence / quiet
#   mute yourself / simona mute / mute simona / simona shut up / shut up simona
#       -> touch ~/.simona-mute, kill audio, clear queue (global mute)
#
#   unmute / unmute yourself / simona unmute / unmute simona
#   speak / speak up / voice on / talk to me / speak again
#       -> rm ~/.simona-mute (lifts global mute; claim is independent)
#
#   stop talking / shush / hush
#       -> kill audio + clear queue (mute flag UNTOUCHED, claim UNTOUCHED)
#
#   speak here / listen here / voice here / claim voice
#       -> set this session as the active speaker
#
#   release voice / silence here / stop speaking here / unclaim voice
#       -> clear the active speaker (back to default silent)
#
# Anything else passes through to the model.

set -euo pipefail

ACTIVE_FILE="/tmp/simona-active-session.id"

_kill_audio() {
  # SIGKILL on the Python procs — their main thread is blocked in
  # subprocess.run(afplay) and a polite SIGTERM loses a race against the
  # consumer loop popping the next queued sentence.
  pkill -9 -f "mcp/kokoro/cli.py"     2>/dev/null || true
  pkill -9 -f "mcp/kokoro/drainer.py" 2>/dev/null || true
  pkill -x afplay                     2>/dev/null || true
  rm -rf /tmp/simona-queue 2>/dev/null || true
  rm -f  /tmp/simona-drainer.pid /tmp/simona-last-queued.ts 2>/dev/null || true
}

input=$(cat)
prompt=$(printf '%s' "$input" | jq -r '.prompt // empty')
session_id=$(printf '%s' "$input" | jq -r '.session_id // empty')

norm=$(printf '%s' "$prompt" \
  | tr '[:upper:]' '[:lower:]' \
  | tr -s '[:punct:]' ' ' \
  | awk '{$1=$1;print}')

flag="$HOME/.simona-mute"

case "$norm" in
  mute|"shut up"|shutup|"be quiet"|"stay quiet"|silence|quiet \
  |"mute yourself"|"simona mute"|"mute simona" \
  |"simona mute yourself"|"mute yourself simona" \
  |"simona shut up"|"shut up simona")
    touch "$flag"
    _kill_audio
    echo "Muted globally. 'unmute' to lift." >&2
    exit 2
    ;;
  unmute|"unmute yourself"|"simona unmute"|"unmute simona" \
  |speak|"speak up"|"voice on"|"talk to me"|"speak again")
    rm -f "$flag"
    echo "Global mute lifted. (Claim is separate — say 'speak here' to claim.)" >&2
    exit 2
    ;;
  "stop talking"|shush|hush)
    _kill_audio
    echo "Stopped current playback." >&2
    exit 2
    ;;
  "speak here"|"listen here"|"voice here"|"claim voice"|"speak in this session" \
  |"speak this session"|"talk here")
    if [ -z "$session_id" ]; then
      echo "Could not determine session ID; claim failed." >&2
      exit 2
    fi
    prev_active=$(cat "$ACTIVE_FILE" 2>/dev/null || echo "")
    if [ "$prev_active" != "$session_id" ]; then
      _kill_audio  # cleanly cut off any audio belonging to the prior speaker
    fi
    printf '%s' "$session_id" > "$ACTIVE_FILE"
    echo "Speaking here. Other sessions stay silent." >&2
    exit 2
    ;;
  "release voice"|"silence here"|"stop speaking here"|"unclaim voice" \
  |"stop speaking in this session"|"release"|"unclaim")
    active=$(cat "$ACTIVE_FILE" 2>/dev/null || echo "")
    if [ "$active" = "$session_id" ]; then
      rm -f "$ACTIVE_FILE"
      _kill_audio
      echo "Voice released. No session is speaking." >&2
    else
      echo "This session isn't the active speaker; nothing to release." >&2
    fi
    exit 2
    ;;
esac

# Pass-through: a real prompt. We don't auto-claim. But if THIS session is
# already the active speaker, cut off any leftover audio so the new turn
# starts clean. Other sessions don't touch the audio state at all.
active=$(cat "$ACTIVE_FILE" 2>/dev/null || echo "")
if [ -n "$session_id" ] && [ "$session_id" = "$active" ]; then
  _kill_audio
fi

exit 0
