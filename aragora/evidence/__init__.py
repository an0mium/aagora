"""Evidence collection and verification module."""

from aragora.evidence.collector import (
    EvidenceCollector,
    EvidenceSnippet,
    EvidencePack,
)

# Import Evidence from connectors where it's defined
from aragora.connectors.base import Evidence

# Import EvidenceType from reasoning where it's defined
from aragora.reasoning.claims import EvidenceType

__all__ = [
    "EvidenceCollector",
    "EvidenceSnippet",
    "EvidencePack",
    "Evidence",
    "EvidenceType",
]
