"""
Debate orchestration module.
"""

from aagora.debate.orchestrator import Arena, DebateProtocol
from aagora.debate.graph import (
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
from aagora.debate.scenarios import (
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
