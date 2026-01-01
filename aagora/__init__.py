"""
aagora (Agent Agora): A Multi-Agent Debate Framework

A society of heterogeneous AI agents that discuss, critique, improve
each other's responses, and learn from successful patterns.

Inspired by:
- Stanford Generative Agents (memory + reflection)
- ChatArena (game environments)
- LLM Multi-Agent Debate (consensus mechanisms)
- UniversalBackrooms (multi-model conversations)
- Project Sid (emergent civilization)
"""

from aagora.core import Agent, Critique, DebateResult, Environment
from aagora.debate.orchestrator import Arena
from aagora.memory.store import CritiqueStore

__version__ = "0.1.0"
__all__ = ["Agent", "Critique", "DebateResult", "Environment", "Arena", "CritiqueStore"]
