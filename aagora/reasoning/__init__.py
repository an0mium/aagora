"""
Reasoning primitives for structured debates.

Provides typed claims, evidence tracking, logical inference,
and cryptographic provenance for evidence.
"""

from aagora.reasoning.claims import (
    ClaimsKernel,
    TypedClaim,
    TypedEvidence,
    ClaimType,
    RelationType,
    EvidenceType,
    ClaimRelation,
    ArgumentChain,
    SourceReference,
)
from aagora.reasoning.provenance import (
    ProvenanceManager,
    ProvenanceChain,
    ProvenanceRecord,
    ProvenanceVerifier,
    CitationGraph,
    Citation,
    MerkleTree,
    SourceType,
    TransformationType,
)

__all__ = [
    # Claims
    "ClaimsKernel",
    "TypedClaim",
    "TypedEvidence",
    "ClaimType",
    "RelationType",
    "EvidenceType",
    "ClaimRelation",
    "ArgumentChain",
    "SourceReference",
    # Provenance
    "ProvenanceManager",
    "ProvenanceChain",
    "ProvenanceRecord",
    "ProvenanceVerifier",
    "CitationGraph",
    "Citation",
    "MerkleTree",
    "SourceType",
    "TransformationType",
]
