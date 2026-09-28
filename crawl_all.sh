#!/usr/bin/env bash
# =============================================================================
# 🤖 AGENT PROJECT METADATA
# Project ID: zhihubf
# Registry:             ~/agent_projects/projects.json
# Manifest:              ~/agent_projects/zhihubf/metadata.json
# Version:                 4.0.0
# Status:          Stable
# Owner:           Agent/User
# =============================================================================

# All-in-one: Launch Edge + run crawl + keep Edge alive during execution
# This prevents macOS from killing Edge between launch and crawl

# Edge user data dir - override via EDGE_PROFILE env var
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EDGE_PROFILE="${EDGE_PROFILE:-$SCRIPT_DIR/edge_agent_profile}"
EDGE_PORT=9222
CDP_URL="127.0.0.1:$EDGE_PORT"

echo "=== Zhihu Crawler - Edge + Crawl ==="

# Step 1: Kill existing Edge
lsof -ti :$EDGE_PORT 2>/dev/null | xargs -r kill 2>/dev/null
sleep 2

# Step 2: Launch Edge with macOS open command
echo "🚀 Launching Edge..."
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
       --disable-backgrounding-occluded-windows
sleep 15

# Step 3: Verify CDP
if ! lsof -i :$EDGE_PORT >/dev/null 2>&1; then
    echo "❌ CDP port not available, aborting"
    exit 1
fi
echo "✅ CDP ready"

# Step 4: Run crawl
cd "$SCRIPT_DIR"
echo "📝 Running crawler (use --user to specify target)..."
python3 run.py "$@"

echo ""
echo "🔒 Keeping Edge alive for 5 minutes..."
sleep 300
echo "Done."
