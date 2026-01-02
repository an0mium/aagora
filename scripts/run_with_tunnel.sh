#!/bin/bash
# Run nomic loop with Cloudflare Tunnel for public access
#
# This exposes your local WebSocket server to the internet via Cloudflare Tunnel.
# The tunnel URL can be used with live.aragora.ai by setting NEXT_PUBLIC_WS_URL.
#
# Prerequisites:
#   - cloudflared installed (brew install cloudflared)
#   - Cloudflare account (for persistent tunnels) or use quick tunnels
#
# Usage:
#   ./scripts/run_with_tunnel.sh [cycles]
#
# For production (api.aragora.ai):
#   You need a Cloudflare Tunnel configured to route api.aragora.ai to localhost:8765

set -e

CYCLES=${1:-3}
SCRIPT_DIR="$(dirname "$0")"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "========================================"
echo "ARAGORA NOMIC LOOP WITH TUNNEL"
echo "========================================"

# Check for cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "ERROR: cloudflared not found. Install with: brew install cloudflared"
    exit 1
fi

# Start cloudflared tunnel in background (quick tunnel - generates random URL)
echo "Starting Cloudflare Tunnel..."
cloudflared tunnel --url http://localhost:8765 &
TUNNEL_PID=$!

# Give tunnel time to establish
sleep 3

echo ""
echo "Tunnel started. Look for the tunnel URL above (*.trycloudflare.com)"
echo ""
echo "To use with live.aragora.ai, update the WS_URL in the dashboard."
echo "Or run the local dashboard: ./scripts/run_live_local.sh"
echo ""
echo "========================================"
echo ""

# Run nomic loop
cd "$PROJECT_DIR"
python scripts/run_nomic_with_stream.py run --cycles "$CYCLES"

# Cleanup
echo "Stopping tunnel..."
kill $TUNNEL_PID 2>/dev/null || true
