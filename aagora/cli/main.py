#!/usr/bin/env python3
"""
Agora CLI - Multi-Agent Debate Framework

Usage:
    agora ask "Design a rate limiter" --agents codex,claude --rounds 3
    agora debate --task "Implement auth system" --agents codex,claude,openai
    agora stats
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aagora.agents.base import create_agent
from aagora.debate.orchestrator import Arena, DebateProtocol
from aagora.memory.store import CritiqueStore
from aagora.core import Environment


def parse_agents(agents_str: str) -> list[tuple[str, str]]:
    """Parse agent string like 'codex,claude:critic,openai'."""
    agents = []
    for spec in agents_str.split(","):
        spec = spec.strip()
        if ":" in spec:
            agent_type, role = spec.split(":", 1)
        else:
            agent_type = spec
            role = None
        agents.append((agent_type, role))
    return agents


async def run_debate(
    task: str,
    agents_str: str,
    rounds: int = 3,
    consensus: str = "majority",
    context: str = "",
    learn: bool = True,
    db_path: str = "agora_memory.db",
):
    """Run a multi-agent debate."""

    # Parse and create agents
    agent_specs = parse_agents(agents_str)

    # Assign default roles
    roles = ["proposer", "critic", "synthesizer"]
    agents = []
    for i, (agent_type, role) in enumerate(agent_specs):
        if role is None:
            if i == 0:
                role = "proposer"
            elif i == len(agent_specs) - 1:
                role = "synthesizer"
            else:
                role = "critic"

        agent = create_agent(
            model_type=agent_type,
            name=f"{agent_type}_{role}",
            role=role,
        )
        agents.append(agent)

    # Create environment
    env = Environment(
        task=task,
        context=context,
        max_rounds=rounds,
    )

    # Create protocol
    protocol = DebateProtocol(
        rounds=rounds,
        consensus=consensus,
    )

    # Create memory store
    memory = CritiqueStore(db_path) if learn else None

    # Run debate
    arena = Arena(env, agents, protocol, memory)
    result = await arena.run()

    # Store result
    if memory:
        memory.store_debate(result)

    return result


def cmd_ask(args):
    """Handle 'ask' command."""
    result = asyncio.run(
        run_debate(
            task=args.task,
            agents_str=args.agents,
            rounds=args.rounds,
            consensus=args.consensus,
            context=args.context or "",
            learn=args.learn,
            db_path=args.db,
        )
    )

    print("\n" + "=" * 60)
    print("FINAL ANSWER:")
    print("=" * 60)
    print(result.final_answer)

    if result.dissenting_views and args.verbose:
        print("\n" + "-" * 60)
        print("DISSENTING VIEWS:")
        for view in result.dissenting_views:
            print(f"\n{view}")


def cmd_stats(args):
    """Handle 'stats' command."""
    store = CritiqueStore(args.db)
    stats = store.get_stats()

    print("\nAgora Memory Statistics")
    print("=" * 40)
    print(f"Total debates: {stats['total_debates']}")
    print(f"Consensus reached: {stats['consensus_debates']}")
    print(f"Total critiques: {stats['total_critiques']}")
    print(f"Total patterns: {stats['total_patterns']}")
    print(f"Avg consensus confidence: {stats['avg_consensus_confidence']:.1%}")

    if stats["patterns_by_type"]:
        print("\nPatterns by type:")
        for ptype, count in sorted(stats["patterns_by_type"].items(), key=lambda x: -x[1]):
            print(f"  {ptype}: {count}")


def cmd_patterns(args):
    """Handle 'patterns' command."""
    store = CritiqueStore(args.db)
    patterns = store.retrieve_patterns(
        issue_type=args.type,
        min_success=args.min_success,
        limit=args.limit,
    )

    print(f"\nTop {len(patterns)} Patterns")
    print("=" * 60)

    for p in patterns:
        print(f"\n[{p.issue_type}] (success: {p.success_count}, severity: {p.avg_severity:.1f})")
        print(f"  Issue: {p.issue_text[:80]}...")
        if p.suggestion_text:
            print(f"  Suggestion: {p.suggestion_text[:80]}...")


def main():
    parser = argparse.ArgumentParser(
        description="Agora - Multi-Agent Debate Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agora ask "Design a rate limiter" --agents codex,claude
  agora ask "Implement auth" --agents codex,claude,openai --rounds 4
  agora stats
  agora patterns --type security
        """,
    )

    parser.add_argument("--db", default="agora_memory.db", help="SQLite database path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Run a multi-agent debate")
    ask_parser.add_argument("task", help="The task/question to debate")
    ask_parser.add_argument(
        "--agents",
        "-a",
        default="codex,claude",
        help="Comma-separated agents (codex,claude,openai). Use agent:role for specific roles.",
    )
    ask_parser.add_argument("--rounds", "-r", type=int, default=3, help="Number of debate rounds")
    ask_parser.add_argument(
        "--consensus",
        "-c",
        choices=["majority", "unanimous", "judge", "none"],
        default="majority",
        help="Consensus mechanism",
    )
    ask_parser.add_argument("--context", help="Additional context for the task")
    ask_parser.add_argument(
        "--no-learn", dest="learn", action="store_false", help="Don't store patterns"
    )
    ask_parser.set_defaults(func=cmd_ask)

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show memory statistics")
    stats_parser.set_defaults(func=cmd_stats)

    # Patterns command
    patterns_parser = subparsers.add_parser("patterns", help="Show learned patterns")
    patterns_parser.add_argument("--type", "-t", help="Filter by issue type")
    patterns_parser.add_argument("--min-success", type=int, default=1, help="Minimum success count")
    patterns_parser.add_argument("--limit", "-l", type=int, default=10, help="Max patterns to show")
    patterns_parser.set_defaults(func=cmd_patterns)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
