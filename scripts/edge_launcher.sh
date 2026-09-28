#!/usr/bin/env bash
# =============================================================================
# 🤖 AGENT PROJECT METADATA
# Project ID: zhihubf
# Registry:            ~/agent_projects/projects.json
# Manifest:             ~/agent_projects/zhihubf/metadata.json
# Version:                4.0.0
# Status:          Stable
# Owner:           User
# =============================================================================

# Edge Agent Profile Launcher - Persistent background process manager
# Usage: ./edge_launcher.sh [start|stop|status|restart]

# Edge binary path - change if needed
EDGE_BIN="${EDGE_BIN:-/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge}"
# Edge user data dir - override via EDGE_PROFILE env var
EDGE_PROFILE="${EDGE_PROFILE:-$(cd "$(dirname "$0")" && pwd)/edge_agent_profile}"
EDGE_PORT=9222
EDGE_PID_FILE="/tmp/edge_agent.pid"
EDGE_LOG="/tmp/edge_agent.log"

# Get actual Edge PID from port 9222 (not from our process)
get_edge_pid() {
    lsof -ti :$EDGE_PORT 2>/dev/null | head -1
}

wait_for_cdp() {
    for i in $(seq 1 30); do
        sleep 1
        if lsof -i :$EDGE_PORT >/dev/null 2>&1; then
            echo "✅ CDP port 9222 UP after ${i}s"
            return 0
        fi
        if [ $i -eq 30 ]; then
            echo "❌ TIMEOUT waiting for CDP port"
            tail -10 "$EDGE_LOG" 2>/dev/null
            return 1
        fi
    done
}

start() {
     # Check if Edge is already running on port 9222
    local existing_pid
    existing_pid=$(get_edge_pid)
    if [ -n "$existing_pid" ]; then
        echo "ℹ️  Edge already running on port 9222 (PID: $existing_pid)"
        return 0
    fi
    
    echo "🚀 Starting Edge Agent Profile..."
    nohup "$EDGE_BIN" \
         --user-data-dir="$EDGE_PROFILE" \
         --remote-debugging-port=$EDGE_PORT \
         --no-first-run \
         --no-default-browser-check \
         --disable-background-timer-throttling \
         --disable-backgrounding-occluded-windows \
         --disable-renderer-backgrounding \
         --disk-cache-dir="/tmp/edge_cache" \
         --media-cache-size=100000000 \
         </dev/null >"$EDGE_LOG" 2>&1 &
    
    echo "Edge PID: $!"
    
    if wait_for_cdp; then
        echo "✅ Edge started successfully"
        return 0
    else
        echo "❌ Edge failed to start"
        return 1
    fi
}

stop() {
    local pid
    pid=$(get_edge_pid)
    if [ -z "$pid" ]; then
        echo "ℹ️  Edge not running on port 9222"
        return 0
    fi
    
    echo "🛑 Stopping Edge (PID: $pid)..."
    kill "$pid" 2>/dev/null
    sleep 3
    
     # Check if still running, force kill if needed
    if kill -0 "$pid" 2>/dev/null; then
        echo "   Force killing..."
        kill -9 "$pid" 2>/dev/null
        sleep 1
    fi
    
    echo "✅ Edge stopped"
}

status() {
    local pid
    pid=$(get_edge_pid)
    if [ -n "$pid" ]; then
        local ps_output
        ps_output=$(ps -p "$pid" -o pid,ppid,stat,etime,args 2>/dev/null | tail -1)
        echo "Edge is RUNNING:"
        echo "   $ps_output"
    else
        echo "Edge is NOT running"
    fi
}

case "${1:-start}" in
    start)  start ;;
    stop)   stop ;;
    restart) stop; sleep 2; start ;;
    status) status ;;
     *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
         ;;
esac
