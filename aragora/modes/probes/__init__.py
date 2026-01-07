"""
Capability probing system for adversarial testing.

This package provides tools for probing agent capabilities to find:
- Self-contradictions
- Hallucinated evidence
- Sycophantic behavior
- Premature concession
- Calibration issues
- Reasoning depth gaps
- Edge case failures
"""

from .models import (
    ProbeType,
    VulnerabilitySeverity,
    ProbeResult,
    VulnerabilityReport,
)
from .strategies import (
    ProbeStrategy,
    ContradictionTrap,
    HallucinationBait,
    SycophancyTest,
    PersistenceChallenge,
    ConfidenceCalibrationProbe,
    ReasoningDepthProbe,
    EdgeCaseProbe,
    STRATEGIES,
)

__all__ = [
    # Models
    "ProbeType",
    "VulnerabilitySeverity",
    "ProbeResult",
    "VulnerabilityReport",
    # Strategy base
    "ProbeStrategy",
    # Concrete strategies
    "ContradictionTrap",
    "HallucinationBait",
    "SycophancyTest",
    "PersistenceChallenge",
    "ConfidenceCalibrationProbe",
    "ReasoningDepthProbe",
    "EdgeCaseProbe",
    # Registry
    "STRATEGIES",
]
