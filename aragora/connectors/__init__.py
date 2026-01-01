"""
Evidence Connectors - Ground debates in real data.

Connectors fetch evidence from external sources and integrate
with the provenance system for traceability:

- LocalDocsConnector: Search local documentation, markdown, code
- GitHubConnector: Fetch issues, PRs, discussions
- WebConnector: Search and fetch web content (future)

All connectors record evidence through ProvenanceManager
with proper source typing and confidence scoring.
"""

from aragora.connectors.local_docs import LocalDocsConnector
from aragora.connectors.github import GitHubConnector
from aragora.connectors.base import BaseConnector, Evidence

__all__ = [
    "BaseConnector",
    "Evidence",
    "LocalDocsConnector",
    "GitHubConnector",
]
