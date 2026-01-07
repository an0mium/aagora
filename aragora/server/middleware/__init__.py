"""
Aragora Server Middleware Package.

Provides composable middleware decorators for common cross-cutting concerns:
- Authentication (require_auth, optional_auth)
- Rate limiting (rate_limit, RateLimiter)
- Caching (cache, ttl_cache)

Usage:
    from aragora.server.middleware import require_auth, rate_limit, cache

    @require_auth
    @rate_limit(requests_per_minute=30)
    @cache(ttl_seconds=300)
    def get_leaderboard(self, handler):
        ...

Middleware can be stacked in any order, but recommended order is:
1. Authentication (first - reject unauthorized requests early)
2. Rate limiting (second - prevent abuse before expensive operations)
3. Caching (last - serve cached responses when available)
"""

from .auth import (
    require_auth,
    require_auth_or_localhost,
    optional_auth,
    extract_token,
    validate_token,
    extract_client_ip,
    AuthContext,
)
from .rate_limit import (
    rate_limit,
    RateLimiter,
    get_rate_limiter,
    cleanup_rate_limiters,
)
from .cache import (
    cache,
    ttl_cache,
    clear_cache,
    invalidate_cache,
    get_cache_stats,
    CacheConfig,
    CACHE_INVALIDATION_MAP,
)

__all__ = [
    # Auth
    "require_auth",
    "require_auth_or_localhost",
    "optional_auth",
    "extract_token",
    "validate_token",
    "extract_client_ip",
    "AuthContext",
    # Rate limiting
    "rate_limit",
    "RateLimiter",
    "get_rate_limiter",
    "cleanup_rate_limiters",
    # Caching
    "cache",
    "ttl_cache",
    "clear_cache",
    "invalidate_cache",
    "get_cache_stats",
    "CacheConfig",
    "CACHE_INVALIDATION_MAP",
]
