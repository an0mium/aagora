"""
Debate phase modules for orchestrator decomposition.

This package contains extracted phase-specific logic from the Arena class
to reduce the orchestrator's complexity and improve maintainability.

Phases:
- voting: Vote collection and aggregation
- critique: Critique selection and routing
- judgment: Judge selection and final decisions
- roles_manager: Role and stance assignment
- spectator: Event emission and spectator notifications
"""

from aragora.debate.phases.voting import VotingPhase
from aragora.debate.phases.critique import CritiquePhase
from aragora.debate.phases.judgment import JudgmentPhase
from aragora.debate.phases.roles_manager import RolesManager
from aragora.debate.phases.spectator import SpectatorMixin

__all__ = [
    "VotingPhase",
    "CritiquePhase",
    "JudgmentPhase",
    "RolesManager",
    "SpectatorMixin",
]
