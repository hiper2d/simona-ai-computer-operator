#!/usr/bin/env bash
# Start Chrome with remote debugging enabled on port 9222.
# Uses a temporary profile to avoid conflicting with your regular Chrome session.
# Copies cookies from default profile so you stay logged in.

set -euo pipefail

PORT="${1:-9222}"

# Check if something is already listening on the port
if command -v lsof &>/dev/null && lsof -i ":$PORT" &>/dev/null; then
    echo "Chrome debug port $PORT is already in use."
    echo "Verify with: curl -s http://localhost:$PORT/json/version | python3 -m json.tool"
    exit 0
fi

# Detect OS and set Chrome path
case "$(uname -s)" in
    Darwin)
        CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        DEFAULT_PROFILE="$HOME/Library/Application Support/Google/Chrome/Default"
        ;;
    Linux)
        CHROME="$(command -v google-chrome || command -v google-chrome-stable || command -v chromium-browser || command -v chromium || echo "")"
        DEFAULT_PROFILE="$HOME/.config/google-chrome/Default"
        ;;
    *)
        echo "Unsupported OS: $(uname -s)"
        exit 1
        ;;
esac

if [ -z "$CHROME" ] || [ ! -f "$CHROME" ] && [ ! -x "$CHROME" ]; then
    echo "Chrome not found. Install Google Chrome first."
    exit 1
fi

# Create temp profile directory
PROFILE_DIR=$(mktemp -d -t chrome-cdp-XXXXXX)
PROFILE_DEFAULT="$PROFILE_DIR/Default"
mkdir -p "$PROFILE_DEFAULT"

echo "Using temp profile: $PROFILE_DIR"

# Copy profile data from default Chrome so we stay logged in.
# We copy the whole Default/ directory (cookies, login data, local storage,
# extensions, etc.) and the Local State file (holds the encryption key for
# cookies/passwords on macOS).  Individual file copies don't work reliably
# because Chrome uses SQLite WAL and the DB is locked while Chrome is running.
CHROME_DATA_DIR="$(dirname "$DEFAULT_PROFILE")"
if [ -d "$DEFAULT_PROFILE" ]; then
    echo "Copying profile from $DEFAULT_PROFILE (this may take a moment)..."
    # rsync is faster than cp for large dirs and handles sparse/locked files better
    if command -v rsync &>/dev/null; then
        rsync -a --quiet "$DEFAULT_PROFILE/" "$PROFILE_DEFAULT/"
    else
        cp -a "$DEFAULT_PROFILE/." "$PROFILE_DEFAULT/" 2>/dev/null || true
    fi
    # Local State lives one level up and holds the key for encrypted cookies
    if [ -f "$CHROME_DATA_DIR/Local State" ]; then
        cp "$CHROME_DATA_DIR/Local State" "$PROFILE_DIR/" 2>/dev/null || true
    fi
    echo "Copied profile data (cookies, passwords, extensions, local storage)."
else
    echo "Warning: Default Chrome profile not found at $DEFAULT_PROFILE"
    echo "Starting with a clean profile."
fi

echo "Starting Chrome on debug port $PORT..."
echo "Press Ctrl+C to stop."

"$CHROME" \
    --remote-debugging-port="$PORT" \
    --user-data-dir="$PROFILE_DIR" \
    --no-first-run \
    --no-default-browser-check \
    --disable-background-timer-throttling \
    --disable-backgrounding-occluded-windows \
    --disable-renderer-backgrounding \
    "about:blank" &

CHROME_PID=$!
echo "Chrome PID: $CHROME_PID"

# Cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down Chrome (PID $CHROME_PID)..."
    kill "$CHROME_PID" 2>/dev/null || true
    sleep 1
    rm -rf "$PROFILE_DIR" 2>/dev/null || true
    echo "Cleaned up temp profile."
}
trap cleanup EXIT INT TERM

# Wait for Chrome to be ready
for i in $(seq 1 15); do
    if curl -s "http://localhost:$PORT/json/version" &>/dev/null; then
        echo "Chrome is ready on http://localhost:$PORT"
        echo "WebSocket targets: http://localhost:$PORT/json/list"
        break
    fi
    sleep 1
done

# Keep the script running
wait "$CHROME_PID"
