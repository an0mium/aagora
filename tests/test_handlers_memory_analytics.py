"""
Tests for MemoryAnalyticsHandler - memory tier analytics endpoints.

Tests cover:
- GET /api/memory/analytics - Get comprehensive analytics
- GET /api/memory/analytics/tier/{tier} - Get tier-specific stats
- POST /api/memory/analytics/snapshot - Take analytics snapshot
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from aragora.server.handlers.memory_analytics import MemoryAnalyticsHandler
from aragora.server.handlers.base import clear_cache


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def handler(tmp_path):
    """Create MemoryAnalyticsHandler instance."""
    ctx = {"analytics_db": str(tmp_path / "test_analytics.db")}
    return MemoryAnalyticsHandler(ctx)


@pytest.fixture
def mock_tracker():
    """Create mock TierAnalyticsTracker."""
    tracker = Mock()
    # Mock get_analytics to return an object with to_dict method
    analytics_mock = Mock()
    analytics_mock.to_dict.return_value = {
        "period_days": 30,
        "tier_stats": {},
        "promotion_effectiveness": 0.75,
        "learning_velocity": 0.12,
        "recommendations": ["Increase retention period"],
    }
    tracker.get_analytics.return_value = analytics_mock

    # Mock get_tier_stats
    tier_stats_mock = Mock()
    tier_stats_mock.to_dict.return_value = {
        "tier": "FAST",
        "total_memories": 150,
        "avg_access_count": 5.2,
        "promotion_rate": 0.3,
    }
    tracker.get_tier_stats.return_value = tier_stats_mock

    tracker.take_snapshot.return_value = None

    return tracker


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear caches before and after each test."""
    clear_cache()
    yield
    clear_cache()


# ============================================================================
# Route Recognition Tests
# ============================================================================

class TestMemoryAnalyticsRouting:
    """Tests for memory analytics route recognition."""

    def test_routes_defined(self, handler):
        """Test handler has routes defined."""
        assert "/api/memory/analytics" in handler.ROUTES
        assert "/api/memory/analytics/snapshot" in handler.ROUTES

    def test_can_handle_base_route(self, handler):
        """Test can_handle for base analytics route."""
        assert handler.can_handle("/api/memory/analytics") is True

    def test_can_handle_tier_route(self, handler):
        """Test can_handle for tier-specific route."""
        assert handler.can_handle("/api/memory/analytics/tier/fast") is True
        assert handler.can_handle("/api/memory/analytics/tier/medium") is True
        assert handler.can_handle("/api/memory/analytics/tier/slow") is True
        assert handler.can_handle("/api/memory/analytics/tier/glacial") is True

    def test_cannot_handle_unrelated_routes(self, handler):
        """Test can_handle returns False for unrelated routes."""
        assert handler.can_handle("/api/debates") is False
        assert handler.can_handle("/api/agents") is False


# ============================================================================
# GET /api/memory/analytics Tests
# ============================================================================

class TestGetAnalytics:
    """Tests for getting comprehensive analytics."""

    def test_analytics_unavailable(self):
        """Test 503 when analytics module not available."""
        # Create handler without tracker by patching the import
        ctx = {"analytics_db": ":memory:"}
        handler = MemoryAnalyticsHandler(ctx)

        # Simulate import failure by keeping _tracker as None
        # and preventing tracker property from loading it
        original_tracker_property = type(handler).tracker

        # Mock to always return None
        type(handler).tracker = property(lambda self: None)
        try:
            result = handler.handle("/api/memory/analytics", {}, None)
            assert result is not None
            assert result.status_code == 503
        finally:
            type(handler).tracker = original_tracker_property

    def test_analytics_success(self, handler, mock_tracker):
        """Test successful analytics retrieval."""
        handler._tracker = mock_tracker

        result = handler.handle("/api/memory/analytics", {}, None)

        assert result is not None
        assert result.status_code == 200
        data = json.loads(result.body)
        assert "period_days" in data
        assert "promotion_effectiveness" in data

    def test_analytics_with_days_param(self, handler, mock_tracker):
        """Test analytics with custom days parameter."""
        handler._tracker = mock_tracker

        result = handler.handle("/api/memory/analytics", {"days": "7"}, None)

        assert result is not None
        assert result.status_code == 200
        mock_tracker.get_analytics.assert_called_with(days=7)

    def test_analytics_days_clamped(self, handler, mock_tracker):
        """Test days parameter is clamped to valid range."""
        handler._tracker = mock_tracker

        # Request 0 days, should be clamped to 1
        result = handler.handle("/api/memory/analytics", {"days": "0"}, None)

        assert result is not None
        assert result.status_code == 200
        mock_tracker.get_analytics.assert_called_with(days=1)


# ============================================================================
# GET /api/memory/analytics/tier/{tier} Tests
# ============================================================================

class TestGetTierStats:
    """Tests for getting tier-specific stats."""

    def test_tier_stats_unavailable(self):
        """Test 503 when analytics module not available."""
        ctx = {"analytics_db": ":memory:"}
        handler = MemoryAnalyticsHandler(ctx)
        original_tracker_property = type(handler).tracker

        type(handler).tracker = property(lambda self: None)
        try:
            result = handler.handle("/api/memory/analytics/tier/fast", {}, None)
            assert result is not None
            assert result.status_code == 503
        finally:
            type(handler).tracker = original_tracker_property

    def test_tier_stats_success(self, handler, mock_tracker):
        """Test successful tier stats retrieval."""
        handler._tracker = mock_tracker

        # Try with actual MemoryTier if available
        try:
            from aragora.memory.tier_manager import MemoryTier

            result = handler.handle("/api/memory/analytics/tier/fast", {}, None)
            # Should be 200 if module is available and tier is valid
            assert result.status_code == 200
            data = json.loads(result.body)
            assert "tier" in data
        except ImportError:
            # MemoryTier not available, test that we get 503
            result = handler.handle("/api/memory/analytics/tier/fast", {}, None)
            assert result.status_code == 503

    def test_tier_stats_invalid_tier(self, handler, mock_tracker):
        """Test 400 for invalid tier name."""
        handler._tracker = mock_tracker

        try:
            result = handler.handle("/api/memory/analytics/tier/invalid", {}, None)
            # Could be 400 (invalid) or 503 (module not available)
            assert result.status_code in [400, 503]
            if result.status_code == 400:
                data = json.loads(result.body)
                assert "invalid" in data["error"].lower() or "tier" in data["error"].lower()
        except ImportError:
            pytest.skip("MemoryTier module not available")


# ============================================================================
# POST /api/memory/analytics/snapshot Tests
# ============================================================================

class TestTakeSnapshot:
    """Tests for taking analytics snapshots."""

    def test_snapshot_unavailable(self):
        """Test 503 when analytics module not available."""
        ctx = {"analytics_db": ":memory:"}
        handler = MemoryAnalyticsHandler(ctx)
        original_tracker_property = type(handler).tracker

        type(handler).tracker = property(lambda self: None)
        try:
            result = handler.handle_post("/api/memory/analytics/snapshot", {}, None)
            assert result is not None
            assert result.status_code == 503
        finally:
            type(handler).tracker = original_tracker_property

    def test_snapshot_success(self, handler, mock_tracker):
        """Test successful snapshot."""
        handler._tracker = mock_tracker

        result = handler.handle_post("/api/memory/analytics/snapshot", {}, None)

        assert result is not None
        assert result.status_code == 200
        data = json.loads(result.body)
        assert data["status"] == "success"
        mock_tracker.take_snapshot.assert_called_once()

    def test_snapshot_wrong_path(self, handler, mock_tracker):
        """Test snapshot returns None for wrong path."""
        handler._tracker = mock_tracker

        result = handler.handle_post("/api/memory/analytics/other", {}, None)

        assert result is None


# ============================================================================
# Tracker Lazy Loading Tests
# ============================================================================

class TestTrackerLoading:
    """Tests for tracker lazy loading."""

    def test_tracker_lazy_loaded(self, tmp_path):
        """Test tracker is lazy-loaded on first access."""
        ctx = {"analytics_db": str(tmp_path / "test.db")}
        handler = MemoryAnalyticsHandler(ctx)

        # Initially tracker is None
        assert handler._tracker is None

        # After accessing tracker property, it may be loaded or None (if import fails)
        _ = handler.tracker
        # Don't assert on tracker value since TierAnalyticsTracker may not exist

    def test_tracker_uses_ctx_db_path(self, tmp_path):
        """Test tracker uses database path from context."""
        db_path = str(tmp_path / "custom_analytics.db")
        ctx = {"analytics_db": db_path}
        handler = MemoryAnalyticsHandler(ctx)

        # Verify context is stored
        assert handler.ctx.get("analytics_db") == db_path


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestMemoryAnalyticsErrorHandling:
    """Tests for error handling in memory analytics handler."""

    def test_analytics_exception_handled(self, handler, mock_tracker):
        """Test analytics exceptions are handled gracefully."""
        mock_tracker.get_analytics.side_effect = Exception("DB error")
        handler._tracker = mock_tracker

        result = handler.handle("/api/memory/analytics", {}, None)

        assert result is not None
        assert result.status_code == 500

    def test_tier_stats_exception_handled(self, handler, mock_tracker):
        """Test tier stats exceptions are handled gracefully."""
        mock_tracker.get_tier_stats.side_effect = Exception("Calculation error")
        handler._tracker = mock_tracker

        try:
            result = handler.handle("/api/memory/analytics/tier/fast", {}, None)
            # Could be 500 (exception) or 503 (module not available)
            assert result.status_code in [500, 503]
        except ImportError:
            pytest.skip("MemoryTier module not available")

    def test_snapshot_exception_handled(self, handler, mock_tracker):
        """Test snapshot exceptions are handled gracefully."""
        mock_tracker.take_snapshot.side_effect = Exception("Write error")
        handler._tracker = mock_tracker

        result = handler.handle_post("/api/memory/analytics/snapshot", {}, None)

        assert result is not None
        assert result.status_code == 500
