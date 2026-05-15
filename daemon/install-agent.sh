#!/bin/bash
# Install Simona's long-loop tick as a per-user launchd LaunchAgent.
# Idempotent — safe to re-run; refreshes the plist on each invocation.
#
# Cadence: 7200s (2 hours). Reviews and monitoring don't need
# sub-hourly response.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TICK_PATH="${REPO_ROOT}/daemon/tick.sh"
SIMONA_DIR="${HOME}/.simona-loop"
LOG_PATH="${SIMONA_DIR}/log"
LABEL="com.simona.tick"
PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"
INTERVAL=7200   # 2 hours

if [ ! -x "$TICK_PATH" ]; then
    echo "error: $TICK_PATH not found or not executable" >&2
    exit 1
fi

mkdir -p "$SIMONA_DIR" "$(dirname "$PLIST_PATH")"

if launchctl print "gui/$(id -u)/${LABEL}" >/dev/null 2>&1; then
    echo "agent already loaded — bootout to refresh"
    launchctl bootout "gui/$(id -u)/${LABEL}" || true
fi

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${TICK_PATH}</string>
    </array>
    <key>StartInterval</key>
    <integer>${INTERVAL}</integer>
    <key>RunAtLoad</key>
    <false/>
    <key>StandardOutPath</key>
    <string>${LOG_PATH}</string>
    <key>StandardErrorPath</key>
    <string>${LOG_PATH}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>${HOME}/.local/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"

echo "installed"
echo ""
echo "  plist:    ${PLIST_PATH}"
echo "  label:    ${LABEL}"
echo "  interval: ${INTERVAL}s ($(( INTERVAL / 60 )) min)"
echo "  log:      ${LOG_PATH}"
echo ""
echo "verify:    launchctl print gui/\$(id -u)/${LABEL} | head"
echo "watch log: tail -f ${LOG_PATH}"
echo "pause:     touch ~/.simona-loop/stop"
echo "uninstall: bash daemon/uninstall-agent.sh"
