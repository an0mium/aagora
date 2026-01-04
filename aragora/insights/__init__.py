"""
Aragora Insights - Extract and aggregate learnings from debates.

This module provides tools for:
- Extracting structured insights from completed debates
- Identifying winning argument patterns
- Tracking agent performance and specializations
- Aggregating meta-learnings across debate history

Key components:
- InsightExtractor: Extracts insights from DebateResult
- InsightStore: Persists insights to SQLite
- InsightAggregator: Cross-debate pattern analysis
"""

from aragora.insights.extractor import (
    Insight,
    InsightType,
    DebateInsights,
    InsightExtractor,
)
from aragora.insights.store import InsightStore
from aragora.insights.flip_detector import (
    FlipEvent,
    AgentConsistencyScore,
    FlipDetector,
    format_flip_for_ui,
    format_consistency_for_ui,
)

__all__ = [
    "Insight",
    "InsightType",
    "DebateInsights",
    "InsightExtractor",
    "InsightStore",
    "FlipEvent",
    "AgentConsistencyScore",
    "FlipDetector",
    "format_flip_for_ui",
    "format_consistency_for_ui",
]
