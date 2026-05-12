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
#   stop talking / shush / hush / stop
#       -> kill audio + clear queue; also release the claim if THIS session
#          holds it (so the next turn won't start speaking again). Mute flag
#          UNTOUCHED. Cross-session claim UNTOUCHED.
#
#   pause / pause speaking / pause talking
#       -> SIGSTOP drainer + afplay; nothing destroyed, resume with `continue`
#
#   continue / resume / keep going / continue speaking
#       -> SIGCONT drainer + afplay; playback resumes mid-sentence
#
#   replay / repeat / say again / say that again / repeat that
#       -> kill current playback and re-speak the current turn's text
#          (falls back to previous turn if current buffer is empty)
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
  rm -f  /tmp/simona-paused.flag 2>/dev/null || true
}

_pause_audio() {
  # SIGSTOP'd procs still answer kill -0, so the speak-response.sh
  # spawn-check won't start a duplicate drainer while we're paused.
  pkill -STOP -f "mcp/kokoro/drainer.py" 2>/dev/null || true
  pkill -STOP -x afplay                  2>/dev/null || true
  touch /tmp/simona-paused.flag
}

_continue_audio() {
  pkill -CONT -f "mcp/kokoro/drainer.py" 2>/dev/null || true
  pkill -CONT -x afplay                  2>/dev/null || true
  rm -f /tmp/simona-paused.flag 2>/dev/null || true
}

_replay_audio() {
  local text=""
  if [ -s /tmp/simona-current-text.txt ]; then
    text=$(cat /tmp/simona-current-text.txt)
  elif [ -s /tmp/simona-prev-text.txt ]; then
    text=$(cat /tmp/simona-prev-text.txt)
  fi
  if [ -z "$text" ]; then
    return 1
  fi
  _kill_audio
  mkdir -p /tmp/simona-queue
  printf '%s' "$text" > "/tmp/simona-queue/$(date +%s%N)_replay.txt"
  ( cd "${CLAUDE_PROJECT_DIR:-$HOME/projects/simona-ai-computer-operator}" \
    && uv run python mcp/kokoro/drainer.py >/dev/null 2>&1 ) &
  disown
  return 0
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
  "stop talking"|shush|hush|stop)
    _kill_audio
    active=$(cat "$ACTIVE_FILE" 2>/dev/null || echo "")
    if [ -n "$session_id" ] && [ "$session_id" = "$active" ]; then
      rm -f "$ACTIVE_FILE"
      echo "Stopped current playback and released voice in this session." >&2
    else
      echo "Stopped current playback." >&2
    fi
    exit 2
    ;;
  pause|"pause speaking"|"pause talking"|"hold on"|"one second")
    _pause_audio
    echo "Paused. Say 'continue' to resume." >&2
    exit 2
    ;;
  continue|resume|"keep going"|"continue speaking"|"continue talking"|"go on")
    _continue_audio
    echo "Resumed." >&2
    exit 2
    ;;
  replay|repeat|"say again"|"say that again"|"repeat that"|"play it again")
    if _replay_audio; then
      echo "Replaying last response." >&2
    else
      echo "Nothing to replay." >&2
    fi
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
# starts clean. Also rotate the replay buffer so the previous turn is
# preserved as -prev- and the current buffer starts fresh.
# Other sessions don't touch the audio state at all.
active=$(cat "$ACTIVE_FILE" 2>/dev/null || echo "")
if [ -n "$session_id" ] && [ "$session_id" = "$active" ]; then
  _kill_audio
  if [ -s /tmp/simona-current-text.txt ]; then
    mv /tmp/simona-current-text.txt /tmp/simona-prev-text.txt
  fi
fi

exit 0
