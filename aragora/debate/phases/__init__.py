"""
Debate phase modules for orchestrator decomposition.

This package contains extracted phase-specific logic from the Arena class
to reduce the orchestrator's complexity and improve maintainability.

Phases:
- voting: Vote collection and aggregation
- proposal: Initial proposal generation
- critique: Critique collection and processing
- revision: Proposal revision based on critiques
- judgment: Judge selection and final decisions
- spectator: Event emission and spectator notifications
"""

from aragora.debate.phases.voting import VotingPhase
from aragora.debate.phases.spectator import SpectatorMixin

__all__ = [
    "VotingPhase",
    "SpectatorMixin",
]
