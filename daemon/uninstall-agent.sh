#!/bin/bash
# Uninstall Simona's long-loop LaunchAgent. Idempotent.

set -euo pipefail

LABEL="com.simona.tick"
PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"

if launchctl print "gui/$(id -u)/${LABEL}" >/dev/null 2>&1; then
    launchctl bootout "gui/$(id -u)/${LABEL}"
    echo "agent unloaded"
else
    echo "agent not loaded — nothing to bootout"
fi

if [ -f "$PLIST_PATH" ]; then
    rm -f "$PLIST_PATH"
    echo "plist removed: $PLIST_PATH"
else
    echo "no plist at $PLIST_PATH — nothing to remove"
fi
