"""
Aragora Configuration Package.

This package provides both validated Pydantic settings (new) and
module-level constants (legacy) for configuration.

New code should use the Pydantic settings:
    from aragora.config.settings import get_settings
    settings = get_settings()
    timeout = settings.database.timeout_seconds

Legacy constants are still available for backward compatibility:
    from aragora.config import DEFAULT_RATE_LIMIT

See settings.py for the full validated configuration schema.
"""

# Re-export Pydantic settings for convenient access
from .settings import (
    # Main settings class and accessor
    Settings,
    get_settings,
    reset_settings,
    # Nested settings classes (for type hints)
    AuthSettings,
    RateLimitSettings,
    APILimitSettings,
    DebateSettings,
    AgentSettings,
    CacheSettings,
    DatabaseSettings,
    WebSocketSettings,
    EloSettings,
    BeliefSettings,
    SSLSettings,
    StorageSettings,
    EvidenceSettings,
    # Constants
    ALLOWED_AGENT_TYPES,
)

# Re-export ALL legacy constants for full backward compatibility
# This ensures any code using `from aragora.config import X` works
# without having to explicitly list every constant
from .legacy import *  # noqa: F401,F403

__all__ = [
    # Main settings
    "Settings",
    "get_settings",
    "reset_settings",
    # Nested settings classes
    "AuthSettings",
    "RateLimitSettings",
    "APILimitSettings",
    "DebateSettings",
    "AgentSettings",
    "CacheSettings",
    "DatabaseSettings",
    "WebSocketSettings",
    "EloSettings",
    "BeliefSettings",
    "SSLSettings",
    "StorageSettings",
    "EvidenceSettings",
    # Constants
    "ALLOWED_AGENT_TYPES",
]
