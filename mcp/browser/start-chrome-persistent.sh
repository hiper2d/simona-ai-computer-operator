#!/usr/bin/env bash
# Persistent-profile Chrome for Marlow's balance/stats scraping cron.
#
# Unlike start-chrome.sh (throwaway mktemp profile, deleted on exit), this uses
# a FIXED profile dir so logins persist across runs: you sign into the provider
# consoles once (headful), the cron reuses the cookies headless.
#
# Dedicated profile + non-default port (9223) so it never collides with your
# daily Chrome or the skill's temp profile on 9222.
#
#   bash start-chrome-persistent.sh            # headful (for the one-time login)
#   HEADLESS=1 bash start-chrome-persistent.sh # headless (for the cron)

set -euo pipefail

PORT="${1:-9223}"
PROFILE_DIR="${MARLOW_SCRAPE_PROFILE:-$HOME/.config/marlow/scrape-profile}"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

if [ ! -x "$CHROME" ]; then
    echo "Chrome not found at $CHROME"; exit 1
fi
if command -v lsof &>/dev/null && lsof -i ":$PORT" &>/dev/null; then
    echo "Port $PORT already in use — Chrome may already be running with this profile."
    exit 0
fi

mkdir -p "$PROFILE_DIR"

# String (not array) so empty expansion is safe under `set -u` on bash 3.2
# (macOS default). The headless flags contain no spaces, so word-splitting is fine.
HEADLESS_FLAGS=""
if [ "${HEADLESS:-0}" = "1" ]; then
    HEADLESS_FLAGS="--headless=new --disable-gpu"
fi

echo "Launching Chrome — profile: $PROFILE_DIR, port: $PORT, headless: ${HEADLESS:-0}"
# shellcheck disable=SC2086  # intentional word-split of HEADLESS_FLAGS
"$CHROME" \
    --remote-debugging-port="$PORT" \
    --user-data-dir="$PROFILE_DIR" \
    --no-first-run \
    --no-default-browser-check \
    --disable-background-timer-throttling \
    --disable-backgrounding-occluded-windows \
    --disable-renderer-backgrounding \
    $HEADLESS_FLAGS \
    "about:blank" &

CHROME_PID=$!
echo "Chrome PID: $CHROME_PID"
for _ in $(seq 1 15); do
    if curl -s "http://localhost:$PORT/json/version" &>/dev/null; then
        echo "ready on http://localhost:$PORT"
        break
    fi
    sleep 1
done
wait "$CHROME_PID"
