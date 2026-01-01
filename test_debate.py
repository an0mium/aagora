#!/usr/bin/env python3
"""
Quick test of the aagora multi-agent debate framework.
"""

import asyncio
import sys
sys.path.insert(0, '/Users/armand/Development/aagora')

from aagora.agents import create_agent
from aagora.debate import Arena, DebateProtocol
from aagora.core import Environment
from aagora.memory import CritiqueStore


async def test_simple_debate():
    """Run a simple 2-agent debate using Codex."""

    # Create two codex agents with different roles
    agents = [
        create_agent("codex", name="proposer", role="proposer"),
        create_agent("codex", name="critic", role="critic"),
    ]

    # Define a simple task
    env = Environment(
        task="Design a simple in-memory cache in Python with TTL (time-to-live) support. Keep it under 50 lines.",
        max_rounds=2,
    )

    # Configure debate with just 2 rounds
    protocol = DebateProtocol(
        rounds=2,
        consensus="majority",
    )

    # Create memory store
    memory = CritiqueStore("/tmp/aagora_test.db")

    # Run debate
    arena = Arena(env, agents, protocol, memory)
    result = await arena.run()

    # Print results
    print("\n" + "="*60)
    print("DEBATE SUMMARY")
    print("="*60)
    print(result.summary())

    # Show stats
    print("\nMemory Stats:")
    stats = memory.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    return result


if __name__ == "__main__":
    result = asyncio.run(test_simple_debate())
