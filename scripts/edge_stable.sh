#!/usr/bin/env bash
# Stable Edge Agent Profile Launcher
# This script ensures Edge stays running as a persistent background process

EDGE_BIN="${EDGE_BIN:-/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge}"
EDGE_PROFILE="${EDGE_PROFILE:-$(cd "$(dirname "$0")" && pwd)/edge_agent_profile}"
EDGE_PORT=9222
EDGE_LOG="/tmp/edge_agent_stable.log"

# Clean up any existing Edge processes on port 9222
echo "🧹 Cleaning up existing Edge processes on port 9222..."
lsof -ti :$EDGE_PORT 2>/dev/null | xargs -r kill 2>/dev/null
sleep 2

echo "🚀 Starting Edge Agent Profile..."
# Use nohup and disown to prevent macOS from killing the process
nohup $EDGE_BIN \
     --user-data-dir="$EDGE_PROFILE" \
     --remote-debugging-port=$EDGE_PORT \
     --no-first-run \
     --no-default-browser-check \
     --disable-background-updates \
     --disable-background-networking \
     --disable-sync \
     --disable-features=Update,BackgroundTimerThrottling,BackgroundThrottling,BackgroundMode,KeepAliveForPushServices \
     --disable-domain-reliability \
     --disable-component-update \
     --disable-back-forward-cache \
     --disable-renderer-backgrounding \
     --disable-ipc-fuzzing \
     --metrics-saving-old-logs \
     >"$EDGE_LOG" 2>&1 &

EDGE_PID=$!
echo "Edge PID: $EDGE_PID"

# Wait for CDP port with longer timeout
echo "⏳ Waiting for CDP port (15s)..."
for i in $(seq 1 15); do
    sleep 1
    if lsof -i :$EDGE_PORT >/dev/null 2>&1; then
        echo "✅ CDP port 9222 is UP!"
        lsof -i :$EDGE_PORT | head -2
        exit 0
    fi
    echo "   Waiting... ($i/15)"
done

echo "❌ Timeout waiting for CDP port"
echo "Edge log preview:"
tail -30 "$EDGE_LOG" 2>/dev/null
exit 1
