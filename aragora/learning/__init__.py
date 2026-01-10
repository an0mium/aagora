"""
Aragora Learning Module.

Implements continual learning with Nested Learning paradigm:
- ContinuumMemory: Multi-timescale memory system
- MetaLearner: Self-tuning hyperparameter optimization
"""

from aragora.memory.continuum import (
    ContinuumMemory,
    ContinuumMemoryEntry,
    MemoryTier,
    TierConfig,
    TIER_CONFIGS,
)
from aragora.learning.meta import MetaLearner

__all__ = [
    "ContinuumMemory",
    "ContinuumMemoryEntry",
    "MemoryTier",
    "TierConfig",
    "TIER_CONFIGS",
    "MetaLearner",
]
