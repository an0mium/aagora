"""
Base handler utilities for modular endpoint handlers.

Provides common response formatting, error handling, and utilities
shared across all endpoint modules.
"""

import json
import logging
import os
import time
from collections import OrderedDict
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional, Tuple
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)


# Cache configuration from environment
CACHE_MAX_ENTRIES = int(os.environ.get("ARAGORA_CACHE_MAX_ENTRIES", "1000"))
CACHE_EVICT_PERCENT = float(os.environ.get("ARAGORA_CACHE_EVICT_PERCENT", "0.1"))


class BoundedTTLCache:
    """
    Thread-safe TTL cache with bounded size and LRU eviction.

    Prevents memory leaks by limiting the number of entries and
    evicting oldest entries when the limit is reached.
    """

    def __init__(self, max_entries: int = CACHE_MAX_ENTRIES, evict_percent: float = CACHE_EVICT_PERCENT):
        self._cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._max_entries = max_entries
        self._evict_count = max(1, int(max_entries * evict_percent))
        self._hits = 0
        self._misses = 0

    def get(self, key: str, ttl_seconds: float) -> tuple[bool, Any]:
        """
        Get a value from cache if not expired.

        Returns:
            Tuple of (hit, value). If hit is False, value is None.
        """
        now = time.time()

        if key in self._cache:
            cached_time, cached_value = self._cache[key]
            if now - cached_time < ttl_seconds:
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                self._hits += 1
                return True, cached_value
            else:
                # Expired - remove it
                del self._cache[key]

        self._misses += 1
        return False, None

    def set(self, key: str, value: Any) -> None:
        """Store a value in cache, evicting old entries if necessary."""
        now = time.time()

        # If key exists, update and move to end
        if key in self._cache:
            self._cache[key] = (now, value)
            self._cache.move_to_end(key)
            return

        # Check if we need to evict
        if len(self._cache) >= self._max_entries:
            self._evict_oldest()

        # Add new entry
        self._cache[key] = (now, value)

    def _evict_oldest(self) -> int:
        """Evict oldest entries to make room. Returns count evicted."""
        evicted = 0
        for _ in range(self._evict_count):
            if self._cache:
                self._cache.popitem(last=False)
                evicted += 1
        if evicted > 0:
            logger.debug(f"Cache evicted {evicted} entries (size: {len(self._cache)})")
        return evicted

    def clear(self, key_prefix: str = None) -> int:
        """Clear entries, optionally filtered by prefix."""
        if key_prefix is None:
            count = len(self._cache)
            self._cache.clear()
            return count
        else:
            keys_to_remove = [k for k in self._cache if k.startswith(key_prefix)]
            for k in keys_to_remove:
                del self._cache[k]
            return len(keys_to_remove)

    def __len__(self) -> int:
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        return key in self._cache

    def items(self):
        """Iterate over cache items."""
        return self._cache.items()

    @property
    def stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        return {
            "entries": len(self._cache),
            "max_entries": self._max_entries,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0.0,
        }


# Global bounded cache instance
_cache = BoundedTTLCache()


def ttl_cache(ttl_seconds: float = 60.0, key_prefix: str = "", skip_self: bool = True):
    """
    Decorator for caching function results with TTL expiry.

    Args:
        ttl_seconds: How long to cache results (default 60s)
        key_prefix: Prefix for cache key to namespace different functions
        skip_self: If True, skip first arg (self) when building cache key for methods

    Usage:
        @ttl_cache(ttl_seconds=300, key_prefix="leaderboard")
        def _get_leaderboard(self, limit: int):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip 'self' when building cache key for methods
            cache_args = args[1:] if skip_self and args else args
            # Build cache key from function name, args and kwargs
            cache_key = f"{key_prefix}:{func.__name__}:{cache_args}:{sorted(kwargs.items())}"

            hit, cached_value = _cache.get(cache_key, ttl_seconds)
            if hit:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value

            # Cache miss or expired
            result = func(*args, **kwargs)
            _cache.set(cache_key, result)
            logger.debug(f"Cache miss, stored {cache_key}")
            return result
        return wrapper
    return decorator


def clear_cache(key_prefix: str = None) -> int:
    """Clear cached entries, optionally filtered by prefix.

    Returns number of entries cleared.
    """
    return _cache.clear(key_prefix)


def get_cache_stats() -> dict:
    """Get cache statistics for monitoring."""
    return _cache.stats


@dataclass
class HandlerResult:
    """Result of handling an HTTP request."""
    status_code: int
    content_type: str
    body: bytes
    headers: dict = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


def json_response(data: Any, status: int = 200) -> HandlerResult:
    """Create a JSON response."""
    body = json.dumps(data, default=str).encode('utf-8')
    return HandlerResult(
        status_code=status,
        content_type="application/json",
        body=body,
    )


def error_response(message: str, status: int = 400) -> HandlerResult:
    """Create an error response."""
    return json_response({"error": message}, status=status)


def parse_query_params(query_string: str) -> dict:
    """Parse query string into a dictionary."""
    if not query_string:
        return {}
    params = parse_qs(query_string)
    # Convert single-value lists to just values
    return {k: v[0] if len(v) == 1 else v for k, v in params.items()}


def get_int_param(params: dict, key: str, default: int = 0) -> int:
    """Safely get an integer parameter."""
    try:
        return int(params.get(key, default))
    except (ValueError, TypeError):
        return default


def get_float_param(params: dict, key: str, default: float = 0.0) -> float:
    """Safely get a float parameter."""
    try:
        return float(params.get(key, default))
    except (ValueError, TypeError):
        return default


def get_bool_param(params: dict, key: str, default: bool = False) -> bool:
    """Safely get a boolean parameter."""
    value = params.get(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


class BaseHandler:
    """
    Base class for endpoint handlers.

    Subclasses implement specific endpoint groups and register
    their routes via the `routes` class attribute.
    """

    def __init__(self, server_context: dict):
        """
        Initialize with server context.

        Args:
            server_context: Dict containing shared server resources like
                           storage, elo_system, debate_embeddings, etc.
        """
        self.ctx = server_context

    def get_storage(self):
        """Get debate storage instance."""
        return self.ctx.get("storage")

    def get_elo_system(self):
        """Get ELO system instance."""
        return self.ctx.get("elo_system")

    def get_debate_embeddings(self):
        """Get debate embeddings database."""
        return self.ctx.get("debate_embeddings")

    def get_critique_store(self):
        """Get critique store instance."""
        return self.ctx.get("critique_store")

    def get_nomic_dir(self):
        """Get nomic directory path."""
        return self.ctx.get("nomic_dir")

    def handle(self, path: str, query_params: dict) -> Optional[HandlerResult]:
        """
        Handle a request. Override in subclasses.

        Args:
            path: The request path
            query_params: Parsed query parameters

        Returns:
            HandlerResult if handled, None if not handled by this handler
        """
        return None
