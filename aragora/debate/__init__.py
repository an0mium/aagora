"""
Debate orchestration module.
"""

from aragora.debate.orchestrator import Arena, DebateProtocol
from aragora.debate.graph import (
    DebateGraph,
    DebateNode,
    Branch,
    BranchPolicy,
    BranchReason,
    MergeStrategy,
    MergeResult,
    ConvergenceScorer,
    GraphReplayBuilder,
    GraphDebateOrchestrator,
    NodeType,
)
from aragora.debate.scenarios import (
    ScenarioMatrix,
    Scenario,
    ScenarioType,
    ScenarioResult,
    MatrixResult,
    MatrixDebateRunner,
    ScenarioComparator,
    OutcomeCategory,
    create_scale_scenarios,
    create_risk_scenarios,
    create_time_horizon_scenarios,
)

__all__ = [
    "Arena",
    "DebateProtocol",
    # Graph-based debates
    "DebateGraph",
    "DebateNode",
    "Branch",
    "BranchPolicy",
    "BranchReason",
    "MergeStrategy",
    "MergeResult",
    "ConvergenceScorer",
    "GraphReplayBuilder",
    "GraphDebateOrchestrator",
    "NodeType",
    # Scenario Matrix
    "ScenarioMatrix",
    "Scenario",
    "ScenarioType",
    "ScenarioResult",
    "MatrixResult",
    "MatrixDebateRunner",
    "ScenarioComparator",
    "OutcomeCategory",
    "create_scale_scenarios",
    "create_risk_scenarios",
    "create_time_horizon_scenarios",
]
