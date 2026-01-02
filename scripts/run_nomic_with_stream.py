#!/usr/bin/env python3
"""
Run nomic loop with live streaming dashboard.

This script starts both the unified server (HTTP + WebSocket) and the nomic loop,
with the nomic loop events streaming to connected clients in real-time.

Usage:
    python scripts/run_nomic_with_stream.py run --cycles 3
    python scripts/run_nomic_with_stream.py run --cycles 3 --http-port 8080 --ws-port 8765
"""

import argparse
import asyncio
import sys
from pathlib import Path
from threading import Thread

# Add aragora to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aragora.server.unified_server import UnifiedServer
from scripts.nomic_loop import NomicLoop


async def run_with_streaming(
    cycles: int = 3,
    http_port: int = 8080,
    ws_port: int = 8765,
    aragora_path: Path = None,
):
    """Run nomic loop with streaming enabled."""
    aragora_path = aragora_path or Path(__file__).parent.parent

    # Resolve paths
    static_dir = aragora_path / "aragora" / "live" / "out"
    if not static_dir.exists():
        print(f"Warning: Static directory not found: {static_dir}")
        print("Run 'cd aragora/live && npm run build' to build the dashboard")
        static_dir = None

    nomic_dir = aragora_path / ".nomic"

    # Create unified server
    server = UnifiedServer(
        http_port=http_port,
        ws_port=ws_port,
        static_dir=static_dir,
        nomic_dir=nomic_dir,
    )

    # Get the emitter for the nomic loop
    emitter = server.emitter

    print("=" * 60)
    print("ARAGORA NOMIC LOOP WITH LIVE STREAMING")
    print("=" * 60)
    print(f"Dashboard:    http://localhost:{http_port}")
    print(f"Live view:    https://live.aragora.ai")
    print(f"WebSocket:    ws://localhost:{ws_port}")
    print(f"Cycles:       {cycles}")
    print("=" * 60)
    print()

    # Create nomic loop with stream emitter
    loop = NomicLoop(
        aragora_path=aragora_path,
        max_cycles=cycles,
        stream_emitter=emitter,
    )

    # Start server in background task
    async def run_server():
        await server.start()

    server_task = asyncio.create_task(run_server())

    # Give server time to start
    await asyncio.sleep(1)

    print("Server started. Running nomic loop...")
    print()

    try:
        # Run the nomic loop
        await loop.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        # Cancel server task
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

    print()
    print("Nomic loop complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Run nomic loop with live streaming dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run nomic loop with streaming")
    run_parser.add_argument(
        "--cycles", "-c",
        type=int,
        default=3,
        help="Number of cycles to run (default: 3)",
    )
    run_parser.add_argument(
        "--http-port",
        type=int,
        default=8080,
        help="HTTP port for dashboard (default: 8080)",
    )
    run_parser.add_argument(
        "--ws-port",
        type=int,
        default=8765,
        help="WebSocket port for streaming (default: 8765)",
    )
    run_parser.add_argument(
        "--aragora-path",
        type=Path,
        default=None,
        help="Path to aragora root (default: auto-detect)",
    )

    args = parser.parse_args()

    if args.command == "run":
        asyncio.run(run_with_streaming(
            cycles=args.cycles,
            http_port=args.http_port,
            ws_port=args.ws_port,
            aragora_path=args.aragora_path,
        ))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
