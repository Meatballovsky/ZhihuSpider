#!/usr/bin/env bash
# Use macOS 'open' command to launch Edge properly in background
# This prevents the system from killing it

EDGE_PROFILE="${EDGE_PROFILE:-$(cd "$(dirname "$0")" && pwd)/edge_agent_profile}"
EDGE_PORT=9222

# Kill any existing Edge on port 9222
lsof -ti :$EDGE_PORT 2>/dev/null | xargs -r kill 2>/dev/null
sleep 2

echo "🚀 Starting Edge with macOS 'open' command..."
# Use 'open' to launch Edge - this makes it a proper macOS app process
open -a 'Microsoft Edge' --args \
     --user-data-dir="$EDGE_PROFILE" \
     --remote-debugging-port=$EDGE_PORT \
     --no-first-run \
     --no-default-browser-check \
     --disable-background-updates \
     --disable-component-update \
     --disable-background-timer-throttling \
     --disable-renderer-backgrounding \
     --disable-ipc-fuzzing \
     --disable-backgrounding-occluded-windows \
     --metrics-saving-old-logs

echo "Edge launched. Waiting for CDP port..."
for i in $(seq 1 30); do
    sleep 1
    if lsof -i :$EDGE_PORT >/dev/null 2>&1; then
        echo "✅ CDP port 9222 UP after ${i}s"
        lsof -i :$EDGE_PORT | head -2
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ TIMEOUT"
    fi
done

sleep 3
echo ""
echo "=== Edge processes ==="
ps aux | grep "[M]icrosoft Edge" | head -5
