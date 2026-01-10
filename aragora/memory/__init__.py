"""
Memory and pattern storage module.

Provides:
- CritiqueStore: SQLite-based storage for debate results and patterns
- SemanticRetriever: Embedding-based similarity search
- Pattern: Dataclass for critique patterns
- ConsensusMemory: Persistent storage of debate outcomes
- DissentRetriever: Retrieval of historical dissenting views
- TierManager: Configurable memory tier management
"""

from aragora.memory.store import CritiqueStore, Pattern
from aragora.memory.embeddings import (
    SemanticRetriever,
    OpenAIEmbedding,
    GeminiEmbedding,
    OllamaEmbedding,
)
from aragora.memory.consensus import (
    ConsensusMemory,
    ConsensusRecord,
    ConsensusStrength,
    DissentRecord,
    DissentType,
    DissentRetriever,
    SimilarDebate,
)
from aragora.memory.tier_manager import (
    TierManager,
    TierConfig,
    TierTransitionMetrics,
    MemoryTier,
    get_tier_manager,
)
from aragora.memory.tier_analytics import (
    TierAnalyticsTracker,
    TierStats,
    MemoryUsageEvent,
    MemoryAnalytics,
)

__all__ = [
    "CritiqueStore",
    "Pattern",
    "SemanticRetriever",
    "OpenAIEmbedding",
    "GeminiEmbedding",
    "OllamaEmbedding",
    # Consensus Memory
    "ConsensusMemory",
    "ConsensusRecord",
    "ConsensusStrength",
    "DissentRecord",
    "DissentType",
    "DissentRetriever",
    "SimilarDebate",
    # Tier Management
    "TierManager",
    "TierConfig",
    "TierTransitionMetrics",
    "MemoryTier",
    "get_tier_manager",
    # Tier Analytics
    "TierAnalyticsTracker",
    "TierStats",
    "MemoryUsageEvent",
    "MemoryAnalytics",
]
