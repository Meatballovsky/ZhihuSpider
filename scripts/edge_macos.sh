#!/usr/bin/env bash
# Launch Edge Agent Profile via AppleScript to prevent system termination

EDGE_PROFILE="${EDGE_PROFILE:-$(cd "$(dirname "$0")" && pwd)/edge_agent_profile}"
EDGE_PORT=9222

# Kill any existing Edge on port 9222
lsof -ti :$EDGE_PORT 2>/dev/null | xargs -r kill 2>/dev/null
sleep 2

# Use osascript to launch Edge in background
osascript -e "
    tell application \"Microsoft Edge\"
        activate
    end tell
    delay 1
    do shell script \"/Applications/Microsoft\\\\ Edge.app/Contents/MacOS/Microsoft\\\\ Edge --user-data-dir='${EDGE_PROFILE}' --remote-debugging-port=${EDGE_PORT} --no-first-run --no-default-browser-check --disable-background-updates --disable-component-update --disable-background-timer-throttling --disable-renderer-backgrounding --disable-ipc-fuzzing &\"
" 2>&1

# Wait for CDP
for i in $(seq 1 20); do
    sleep 1
    if lsof -i :$EDGE_PORT >/dev/null 2>&1; then
        echo "✅ CDP UP after ${i}s"
        lsof -i :$EDGE_PORT | head -2
        break
    fi
    if [ $i -eq 20 ]; then
        echo "❌ TIMEOUT"
    fi
done

sleep 3
ps aux | grep "[M]icrosoft Edge" | grep "Agent Profile" | head -3
