"""
Centralized CORS configuration for all Aragora server components.

This module provides a single source of truth for allowed origins,
preventing configuration drift across auth, api, stream, and unified_server.
"""

import os
from typing import Set


# Default allowed origins (covers development + production)
DEFAULT_ORIGINS: Set[str] = {
    # Development
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    # Production
    "https://aragora.ai",
    "https://www.aragora.ai",
    "https://live.aragora.ai",
    "https://api.aragora.ai",
}


class CORSConfig:
    """Centralized CORS configuration with environment variable support."""

    def __init__(self):
        """Initialize CORS config from environment or defaults."""
        env_origins = os.getenv("ARAGORA_ALLOWED_ORIGINS", "").strip()
        if env_origins:
            # Parse comma-separated origins from environment
            self.allowed_origins: Set[str] = {
                o.strip() for o in env_origins.split(",") if o.strip()
            }
        else:
            self.allowed_origins = DEFAULT_ORIGINS.copy()

    def is_origin_allowed(self, origin: str) -> bool:
        """Check if an origin is in the allowlist."""
        return origin in self.allowed_origins

    def get_origins_list(self) -> list[str]:
        """Return allowed origins as a list (for compatibility)."""
        return list(self.allowed_origins)

    def add_origin(self, origin: str) -> None:
        """Add an origin to the allowlist at runtime."""
        self.allowed_origins.add(origin)

    def remove_origin(self, origin: str) -> None:
        """Remove an origin from the allowlist at runtime."""
        self.allowed_origins.discard(origin)


# Singleton instance for import
cors_config = CORSConfig()

# Convenience exports for backwards compatibility
ALLOWED_ORIGINS = cors_config.get_origins_list()
WS_ALLOWED_ORIGINS = ALLOWED_ORIGINS  # Alias for stream.py compatibility
