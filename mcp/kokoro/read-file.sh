#!/bin/bash
# Read a file aloud in background via Kokoro TTS.
#
# Usage:
#   bash mcp/kokoro/read-file.sh <file> [--start N] [--end N]
#
# Sets /tmp/simona-reading.flag while playing so the Stop hook doesn't
# override the file with my own closing text. Stop with `simona-shutup`,
# `shut up` in chat, or `simona-mute` (persistent).

set -euo pipefail

FILE=""
START=""
END=""

while [ $# -gt 0 ]; do
  case "$1" in
    --start) START="$2"; shift 2 ;;
    --end)   END="$2"; shift 2 ;;
    --) shift; break ;;
    *)       FILE="$1"; shift ;;
  esac
done

[ -z "$FILE" ]   && { echo "usage: $0 <file> [--start N] [--end N]" >&2; exit 1; }
[ ! -f "$FILE" ] && { echo "file not found: $FILE" >&2; exit 1; }

if   [ -n "$START" ] && [ -n "$END" ]; then TEXT=$(sed -n "${START},${END}p" "$FILE")
elif [ -n "$START" ];                   then TEXT=$(sed -n "${START},\$p"   "$FILE")
elif [ -n "$END" ];                     then TEXT=$(sed -n "1,${END}p"      "$FILE")
else                                         TEXT=$(cat                     "$FILE")
fi

if [ -z "$(printf '%s' "$TEXT" | tr -d '[:space:]')" ]; then
  echo "no content to read" >&2; exit 1
fi

PROJECT_DIR="/Users/hiper2d/projects/simona-ai-computer-operator"
FLAG="/tmp/simona-reading.flag"

# Kill any in-flight playback first so a new read replaces an old one cleanly
pkill -f "mcp/kokoro/cli.py" 2>/dev/null || true
pkill -x afplay              2>/dev/null || true

touch "$FLAG"
(
  trap 'rm -f "$FLAG"' EXIT INT TERM
  cd "$PROJECT_DIR"
  printf '%s' "$TEXT" | uv run python mcp/kokoro/cli.py speak >/dev/null 2>&1
) &
disown

SUFFIX=""
[ -n "$START" ] && [ -n "$END" ] && SUFFIX=" (lines $START-$END)"
[ -n "$START" ] && [ -z "$END" ] && SUFFIX=" (from line $START)"
[ -z "$START" ] && [ -n "$END" ] && SUFFIX=" (lines 1-$END)"
echo "reading $(basename "$FILE")$SUFFIX — 'shut up' or simona-shutup to stop"
