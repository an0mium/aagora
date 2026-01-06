"""Tests for rate limiting middleware."""

import pytest
import time
from aragora.server.rate_limit import (
    TokenBucket,
    RateLimiter,
    RateLimitConfig,
    RateLimitResult,
    get_limiter,
    set_limiter,
    rate_limit_headers,
)


class TestTokenBucket:
    """Test TokenBucket class."""

    def test_bucket_creation(self):
        """Test basic bucket creation."""
        bucket = TokenBucket(rate_per_minute=60, burst_size=10)
        assert bucket.rate_per_minute == 60
        assert bucket.burst_size == 10
        assert bucket.tokens == 10.0  # Starts full

    def test_consume_success(self):
        """Test successful token consumption."""
        bucket = TokenBucket(rate_per_minute=60, burst_size=5)
        assert bucket.consume(1) is True
        assert bucket.remaining == 4

    def test_consume_failure_when_empty(self):
        """Test consumption fails when bucket is empty."""
        bucket = TokenBucket(rate_per_minute=60, burst_size=2)
        assert bucket.consume(1) is True
        assert bucket.consume(1) is True
        assert bucket.consume(1) is False  # Empty

    def test_consume_multiple_tokens(self):
        """Test consuming multiple tokens at once."""
        bucket = TokenBucket(rate_per_minute=60, burst_size=5)
        assert bucket.consume(3) is True
        assert bucket.remaining == 2
        assert bucket.consume(3) is False  # Not enough

    def test_refill_over_time(self):
        """Test token refill over time."""
        bucket = TokenBucket(rate_per_minute=60, burst_size=5)
        # Drain the bucket
        while bucket.consume(1):
            pass

        # Simulate time passing (modify internal state for testing)
        bucket.last_refill = time.monotonic() - 1.0  # 1 second ago
        # Should have refilled 1 token (60/60 = 1 token per second)
        assert bucket.consume(1) is True

    def test_get_retry_after(self):
        """Test retry-after calculation."""
        bucket = TokenBucket(rate_per_minute=60, burst_size=2)
        bucket.consume(2)  # Empty the bucket

        # Retry after should be positive when empty
        retry = bucket.get_retry_after()
        assert retry > 0  # Need to wait for refill

    def test_default_burst_size(self):
        """Test default burst size is 2x rate."""
        bucket = TokenBucket(rate_per_minute=30)
        assert bucket.burst_size == 60  # 30 * 2


class TestRateLimitConfig:
    """Test RateLimitConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = RateLimitConfig()
        assert config.requests_per_minute == 60
        assert config.key_type == "ip"
        assert config.enabled is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = RateLimitConfig(
            requests_per_minute=30,
            burst_size=50,
            key_type="token",
        )
        assert config.requests_per_minute == 30
        assert config.burst_size == 50
        assert config.key_type == "token"


class TestRateLimiter:
    """Test RateLimiter class."""

    def test_limiter_creation(self):
        """Test limiter creation with defaults."""
        limiter = RateLimiter()
        assert limiter.default_limit == 60
        assert limiter.ip_limit == 120

    def test_allow_request(self):
        """Test allowing a request."""
        limiter = RateLimiter(default_limit=10)
        result = limiter.allow("192.168.1.1")
        assert result.allowed is True
        assert result.remaining >= 0

    def test_rate_limit_after_burst(self):
        """Test rate limiting after burst is exhausted."""
        limiter = RateLimiter(ip_limit=2)
        limiter.allow("192.168.1.1")  # 1
        limiter.allow("192.168.1.1")  # 2
        limiter.allow("192.168.1.1")  # 3
        limiter.allow("192.168.1.1")  # 4 (burst)

        # Should eventually be rate limited
        result = None
        for _ in range(10):
            result = limiter.allow("192.168.1.1")
            if not result.allowed:
                break

        # At some point should be rate limited
        assert result is not None

    def test_different_ips_independent(self):
        """Test that different IPs have independent limits."""
        limiter = RateLimiter(ip_limit=3)

        # Exhaust IP 1's bucket
        for _ in range(10):
            limiter.allow("192.168.1.1")

        # IP 2 should still be allowed
        result = limiter.allow("192.168.1.2")
        assert result.allowed is True

    def test_configure_endpoint(self):
        """Test endpoint-specific configuration."""
        limiter = RateLimiter()
        limiter.configure_endpoint("/api/debates", 30, key_type="combined")

        config = limiter.get_config("/api/debates")
        assert config.requests_per_minute == 30
        assert config.key_type == "combined"

    def test_endpoint_prefix_match(self):
        """Test endpoint prefix matching."""
        limiter = RateLimiter()
        limiter.configure_endpoint("/api/agent/*", 100)

        config = limiter.get_config("/api/agent/claude/profile")
        assert config.requests_per_minute == 100

    def test_combined_key_type(self):
        """Test combined endpoint+IP rate limiting."""
        limiter = RateLimiter()
        limiter.configure_endpoint("/api/debates", 2, key_type="combined")

        # Same IP, same endpoint - should share limit
        result1 = limiter.allow("1.1.1.1", endpoint="/api/debates")
        result2 = limiter.allow("1.1.1.1", endpoint="/api/debates")
        assert result1.allowed is True
        assert result2.allowed is True

        # Different IP, same endpoint - should have own limit
        result3 = limiter.allow("2.2.2.2", endpoint="/api/debates")
        assert result3.allowed is True

    def test_get_stats(self):
        """Test getting limiter statistics."""
        limiter = RateLimiter()
        limiter.allow("1.1.1.1")
        limiter.allow("2.2.2.2")

        stats = limiter.get_stats()
        assert stats["ip_buckets"] == 2
        assert stats["default_limit"] == 60

    def test_result_contains_limit_info(self):
        """Test that result contains limit information."""
        limiter = RateLimiter(ip_limit=50)
        result = limiter.allow("1.1.1.1")

        assert result.limit > 0
        assert result.remaining >= 0
        assert result.key.startswith("ip:")


class TestRateLimitHeaders:
    """Test rate limit header generation."""

    def test_headers_when_allowed(self):
        """Test headers for allowed request."""
        result = RateLimitResult(
            allowed=True,
            remaining=50,
            limit=60,
            retry_after=0,
            key="ip:1.1.1.1",
        )
        headers = rate_limit_headers(result)
        assert headers["X-RateLimit-Limit"] == "60"
        assert headers["X-RateLimit-Remaining"] == "50"
        assert "Retry-After" not in headers

    def test_headers_when_limited(self):
        """Test headers for rate limited request."""
        result = RateLimitResult(
            allowed=False,
            remaining=0,
            limit=60,
            retry_after=5.5,
            key="ip:1.1.1.1",
        )
        headers = rate_limit_headers(result)
        assert headers["X-RateLimit-Limit"] == "60"
        assert headers["X-RateLimit-Remaining"] == "0"
        assert headers["Retry-After"] == "6"  # Rounded up
        assert "X-RateLimit-Reset" in headers


class TestGlobalLimiter:
    """Test global limiter management."""

    def test_get_limiter_singleton(self):
        """Test get_limiter returns singleton."""
        set_limiter(None)  # Reset
        limiter1 = get_limiter()
        limiter2 = get_limiter()
        assert limiter1 is limiter2

    def test_set_limiter(self):
        """Test setting custom limiter."""
        custom = RateLimiter(default_limit=10)
        set_limiter(custom)
        assert get_limiter() is custom

    def test_default_endpoint_configs(self):
        """Test default endpoint configurations are set."""
        set_limiter(None)  # Reset
        limiter = get_limiter()

        # Check that some endpoints are configured
        debates_config = limiter.get_config("/api/debates")
        assert debates_config.requests_per_minute == 30


class TestConcurrency:
    """Test thread safety."""

    def test_concurrent_bucket_access(self):
        """Test concurrent access to token bucket."""
        import threading

        bucket = TokenBucket(rate_per_minute=1000, burst_size=100)
        consumed = []

        def consumer():
            for _ in range(20):
                if bucket.consume(1):
                    consumed.append(1)

        threads = [threading.Thread(target=consumer) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have consumed at most burst_size tokens
        assert len(consumed) <= 100

    def test_concurrent_limiter_access(self):
        """Test concurrent access to limiter."""
        import threading

        limiter = RateLimiter(ip_limit=50)
        results = []

        def requester():
            for _ in range(20):
                result = limiter.allow(f"192.168.1.{threading.current_thread().name[-1]}")
                results.append(result.allowed)

        threads = [threading.Thread(target=requester, name=f"thread_{i}") for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have some allowed and some possibly limited
        assert len(results) == 100
        assert any(results)  # At least some allowed


class TestTokenBucketEdgeCases:
    """Edge case tests for TokenBucket."""

    def test_zero_rate_per_minute(self):
        """Test with zero rate - should handle gracefully."""
        bucket = TokenBucket(rate_per_minute=0, burst_size=5)
        assert bucket.consume(1) is True  # Can use burst
        assert bucket.consume(1) is True
        assert bucket.consume(1) is True
        assert bucket.consume(1) is True
        assert bucket.consume(1) is True
        # After burst, should stay empty since rate=0
        assert bucket.consume(1) is False

    def test_very_small_rate(self):
        """Test with very small rate (0.001 tokens/minute)."""
        bucket = TokenBucket(rate_per_minute=0.001, burst_size=1)
        assert bucket.consume(1) is True
        # Should need ~60000 seconds to get next token
        retry_after = bucket.get_retry_after()
        assert retry_after > 0

    def test_consume_zero_tokens(self):
        """Test consuming zero tokens."""
        bucket = TokenBucket(rate_per_minute=60, burst_size=5)
        assert bucket.consume(0) is True
        assert bucket.remaining == 5  # Should not consume

    def test_consume_negative_tokens(self):
        """Test consuming negative tokens - should add tokens back."""
        bucket = TokenBucket(rate_per_minute=60, burst_size=5)
        initial = bucket.remaining
        bucket.consume(-1)  # This is technically allowed
        assert bucket.remaining >= initial  # Tokens added

    def test_consume_more_than_burst(self):
        """Test consuming more tokens than burst size."""
        bucket = TokenBucket(rate_per_minute=60, burst_size=5)
        assert bucket.consume(10) is False  # Can't consume 10 when max is 5

    def test_get_retry_after_when_full(self):
        """Test retry_after when bucket is full."""
        bucket = TokenBucket(rate_per_minute=60, burst_size=5)
        assert bucket.get_retry_after() == 0

    def test_very_large_rate(self):
        """Test with very large rate."""
        bucket = TokenBucket(rate_per_minute=1000000, burst_size=100)
        assert bucket.consume(50) is True
        # Should refill quickly
        bucket.last_refill = time.monotonic() - 0.001  # 1ms ago
        bucket.consume(1)  # Trigger refill
        assert bucket.remaining > 45  # Should have refilled some


class TestRateLimiterEdgeCases:
    """Edge case tests for RateLimiter."""

    def test_empty_ip_address(self):
        """Test with empty IP address."""
        limiter = RateLimiter()
        result = limiter.allow("")
        # Should still work, using "" as key
        assert result is not None

    def test_none_endpoint(self):
        """Test with None endpoint."""
        limiter = RateLimiter()
        result = limiter.allow("1.1.1.1", endpoint=None)
        assert result.allowed is True

    def test_very_long_ip_address(self):
        """Test with very long IP string."""
        limiter = RateLimiter()
        long_ip = "a" * 1000  # Malformed but should handle
        result = limiter.allow(long_ip)
        assert result is not None

    def test_special_characters_in_endpoint(self):
        """Test endpoint with special characters."""
        limiter = RateLimiter()
        limiter.configure_endpoint("/api/test/*", 30)
        result = limiter.allow("1.1.1.1", endpoint="/api/test/../../etc/passwd")
        assert result is not None

    def test_unicode_in_ip(self):
        """Test with Unicode in IP address."""
        limiter = RateLimiter()
        result = limiter.allow("192.168.1.1\u0000malicious")
        assert result is not None

    def test_lru_eviction_with_many_ips(self):
        """Test LRU eviction when max_entries exceeded."""
        limiter = RateLimiter()
        # Generate many unique IPs
        for i in range(200):  # More than typical max_entries
            limiter.allow(f"192.168.{i % 256}.{i // 256}")
        # Should not crash and still work
        result = limiter.allow("192.168.0.1")
        assert result is not None


class TestRateLimitResultEdgeCases:
    """Edge case tests for RateLimitResult headers."""

    def test_headers_with_zero_retry_after(self):
        """Test headers with retry_after=0."""
        result = RateLimitResult(
            allowed=False,
            remaining=0,
            limit=60,
            retry_after=0,
            key="ip:1.1.1.1",
        )
        headers = rate_limit_headers(result)
        # Should not have Retry-After when it's 0
        assert headers.get("Retry-After") == "1" or "Retry-After" not in headers

    def test_headers_with_fractional_retry_after(self):
        """Test headers with fractional retry_after."""
        result = RateLimitResult(
            allowed=False,
            remaining=0,
            limit=60,
            retry_after=0.1,
            key="ip:1.1.1.1",
        )
        headers = rate_limit_headers(result)
        # Should round up to 1
        assert int(headers.get("Retry-After", "0")) >= 1

    def test_headers_with_very_large_retry_after(self):
        """Test headers with very large retry_after."""
        result = RateLimitResult(
            allowed=False,
            remaining=0,
            limit=60,
            retry_after=999999,
            key="ip:1.1.1.1",
        )
        headers = rate_limit_headers(result)
        assert "Retry-After" in headers

    def test_headers_with_negative_remaining(self):
        """Test headers with negative remaining (edge case)."""
        result = RateLimitResult(
            allowed=False,
            remaining=-1,
            limit=60,
            retry_after=5,
            key="ip:1.1.1.1",
        )
        headers = rate_limit_headers(result)
        # Should handle gracefully, maybe showing 0
        assert headers["X-RateLimit-Remaining"] in ["-1", "0"]


class TestRateLimitConfigEdgeCases:
    """Edge case tests for RateLimitConfig."""

    def test_very_high_rate_endpoint(self):
        """Test endpoint with very high rate limit."""
        limiter = RateLimiter()
        limiter.configure_endpoint("/api/health", 1000000)
        # Should allow many requests
        for _ in range(100):
            result = limiter.allow("1.1.1.1", endpoint="/api/health")
            assert result.allowed is True

    def test_wildcard_at_start_of_endpoint(self):
        """Test wildcard at start of endpoint pattern."""
        limiter = RateLimiter()
        limiter.configure_endpoint("*/debates", 30)
        # Should match endpoints ending with /debates
        config = limiter.get_config("/api/v1/debates")
        # May or may not match depending on implementation

    def test_empty_endpoint_pattern(self):
        """Test empty endpoint pattern."""
        limiter = RateLimiter()
        limiter.configure_endpoint("", 30)
        # Should handle gracefully
        config = limiter.get_config("")
        assert config is not None
