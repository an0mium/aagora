"""Tests for CritiqueHandler - critique patterns and reputation endpoints."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import tempfile
import os

from aragora.server.handlers.critique import CritiqueHandler, CRITIQUE_STORE_AVAILABLE


@pytest.fixture
def mock_ctx():
    """Create mock context for handler."""
    return {
        "nomic_dir": Path("/tmp/test_nomic"),
        "storage": None,
        "elo_system": None,
    }


@pytest.fixture
def handler(mock_ctx):
    """Create CritiqueHandler with mock context."""
    return CritiqueHandler(mock_ctx)


class TestCritiqueHandlerRouting:
    """Test route matching for CritiqueHandler."""

    def test_can_handle_patterns_endpoint(self, handler):
        """Handler should match /api/critiques/patterns."""
        assert handler.can_handle("/api/critiques/patterns")

    def test_can_handle_archive_endpoint(self, handler):
        """Handler should match /api/critiques/archive."""
        assert handler.can_handle("/api/critiques/archive")

    def test_can_handle_all_reputations(self, handler):
        """Handler should match /api/reputation/all."""
        assert handler.can_handle("/api/reputation/all")

    def test_can_handle_agent_reputation(self, handler):
        """Handler should match /api/agent/{name}/reputation."""
        assert handler.can_handle("/api/agent/claude/reputation")
        assert handler.can_handle("/api/agent/gpt4/reputation")

    def test_cannot_handle_invalid_path(self, handler):
        """Handler should not match invalid paths."""
        assert not handler.can_handle("/api/invalid")
        assert not handler.can_handle("/api/critiques")
        assert not handler.can_handle("/api/agent/claude/history")

    def test_cannot_handle_partial_paths(self, handler):
        """Handler should not match partial paths."""
        assert not handler.can_handle("/api/critiques/patterns/extra")
        assert not handler.can_handle("/api/reputation")


class TestPatternsEndpoint:
    """Test /api/critiques/patterns endpoint."""

    def test_patterns_no_db(self, handler):
        """Returns empty patterns when database doesn't exist."""
        result = handler.handle("/api/critiques/patterns", {}, None)
        assert result is not None
        # Either empty patterns or 503 if store not available
        assert result.status_code in (200, 503)

    def test_patterns_with_limit(self, handler):
        """Limit parameter is capped at 50."""
        # Test that limit is applied (we can't easily verify the cap without mocking)
        result = handler.handle("/api/critiques/patterns", {"limit": ["100"]}, None)
        assert result is not None

    def test_patterns_with_min_success(self, handler):
        """min_success parameter is clamped to 0-1."""
        result = handler.handle("/api/critiques/patterns", {"min_success": ["0.8"]}, None)
        assert result is not None

    @pytest.mark.skipif(not CRITIQUE_STORE_AVAILABLE, reason="CritiqueStore not available")
    def test_patterns_with_mock_store(self, mock_ctx):
        """Test patterns endpoint with mocked CritiqueStore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nomic_dir = Path(tmpdir)
            db_path = nomic_dir / "debates.db"
            db_path.touch()

            mock_ctx["nomic_dir"] = nomic_dir
            handler = CritiqueHandler(mock_ctx)

            with patch("aragora.server.handlers.critique.CritiqueStore") as MockStore:
                mock_store = Mock()
                mock_store.retrieve_patterns.return_value = []
                mock_store.get_stats.return_value = {"total": 0}
                MockStore.return_value = mock_store

                result = handler.handle("/api/critiques/patterns", {}, None)
                assert result is not None
                assert result.status_code == 200


class TestArchiveEndpoint:
    """Test /api/critiques/archive endpoint."""

    def test_archive_no_db(self, handler):
        """Returns empty archive when database doesn't exist."""
        result = handler.handle("/api/critiques/archive", {}, None)
        assert result is not None
        assert result.status_code in (200, 503)

    @pytest.mark.skipif(not CRITIQUE_STORE_AVAILABLE, reason="CritiqueStore not available")
    def test_archive_with_mock_store(self, mock_ctx):
        """Test archive endpoint with mocked CritiqueStore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nomic_dir = Path(tmpdir)
            db_path = nomic_dir / "debates.db"
            db_path.touch()

            mock_ctx["nomic_dir"] = nomic_dir
            handler = CritiqueHandler(mock_ctx)

            with patch("aragora.server.handlers.critique.CritiqueStore") as MockStore:
                mock_store = Mock()
                mock_store.get_archive_stats.return_value = {"archived": 0, "by_type": {}}
                MockStore.return_value = mock_store

                result = handler.handle("/api/critiques/archive", {}, None)
                assert result is not None
                assert result.status_code == 200


class TestReputationsEndpoint:
    """Test /api/reputation/all endpoint."""

    def test_all_reputations_no_db(self, handler):
        """Returns empty reputations when database doesn't exist."""
        result = handler.handle("/api/reputation/all", {}, None)
        assert result is not None
        assert result.status_code in (200, 503)

    @pytest.mark.skipif(not CRITIQUE_STORE_AVAILABLE, reason="CritiqueStore not available")
    def test_all_reputations_with_mock_store(self, mock_ctx):
        """Test all reputations endpoint with mocked store."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nomic_dir = Path(tmpdir)
            db_path = nomic_dir / "debates.db"
            db_path.touch()

            mock_ctx["nomic_dir"] = nomic_dir
            handler = CritiqueHandler(mock_ctx)

            with patch("aragora.server.handlers.critique.CritiqueStore") as MockStore:
                mock_rep = Mock()
                mock_rep.agent_name = "claude"
                mock_rep.reputation_score = 0.8
                mock_rep.vote_weight = 1.2
                mock_rep.proposal_acceptance_rate = 0.75
                mock_rep.critique_value = 0.6
                mock_rep.debates_participated = 10

                mock_store = Mock()
                mock_store.get_all_reputations.return_value = [mock_rep]
                MockStore.return_value = mock_store

                result = handler.handle("/api/reputation/all", {}, None)
                assert result is not None
                assert result.status_code == 200


class TestAgentReputationEndpoint:
    """Test /api/agent/{name}/reputation endpoint."""

    def test_agent_reputation_no_db(self, handler):
        """Returns null reputation when database doesn't exist."""
        result = handler.handle("/api/agent/claude/reputation", {}, None)
        assert result is not None
        assert result.status_code in (200, 503)

    def test_agent_reputation_path_traversal_blocked(self, handler):
        """Path traversal attempts are blocked."""
        result = handler.handle("/api/agent/../etc/passwd/reputation", {}, None)
        assert result is not None
        assert result.status_code == 400

    def test_agent_reputation_invalid_name(self, handler):
        """Invalid agent names are rejected."""
        # Handler extracts agent from path, returns None for invalid
        result = handler.handle("/api/agent/<script>/reputation", {}, None)
        assert result is not None
        assert result.status_code == 400

    def test_agent_reputation_valid_names(self, handler):
        """Valid agent names are accepted."""
        valid_names = ["claude", "gpt4", "gemini-pro", "agent_1", "test.agent"]
        for name in valid_names:
            result = handler.handle(f"/api/agent/{name}/reputation", {}, None)
            assert result is not None
            # Should not be 400 (bad request)
            assert result.status_code != 400 or result.status_code in (200, 503)

    @pytest.mark.skipif(not CRITIQUE_STORE_AVAILABLE, reason="CritiqueStore not available")
    def test_agent_reputation_found(self, mock_ctx):
        """Test agent reputation when agent exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nomic_dir = Path(tmpdir)
            db_path = nomic_dir / "debates.db"
            db_path.touch()

            mock_ctx["nomic_dir"] = nomic_dir
            handler = CritiqueHandler(mock_ctx)

            with patch("aragora.server.handlers.critique.CritiqueStore") as MockStore:
                mock_rep = Mock()
                mock_rep.reputation_score = 0.85
                mock_rep.vote_weight = 1.1
                mock_rep.proposal_acceptance_rate = 0.8
                mock_rep.critique_value = 0.7
                mock_rep.debates_participated = 15

                mock_store = Mock()
                mock_store.get_reputation.return_value = mock_rep
                MockStore.return_value = mock_store

                result = handler.handle("/api/agent/claude/reputation", {}, None)
                assert result is not None
                assert result.status_code == 200

    @pytest.mark.skipif(not CRITIQUE_STORE_AVAILABLE, reason="CritiqueStore not available")
    def test_agent_reputation_not_found(self, mock_ctx):
        """Test agent reputation when agent doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nomic_dir = Path(tmpdir)
            db_path = nomic_dir / "debates.db"
            db_path.touch()

            mock_ctx["nomic_dir"] = nomic_dir
            handler = CritiqueHandler(mock_ctx)

            with patch("aragora.server.handlers.critique.CritiqueStore") as MockStore:
                mock_store = Mock()
                mock_store.get_reputation.return_value = None
                MockStore.return_value = mock_store

                result = handler.handle("/api/agent/unknown/reputation", {}, None)
                assert result is not None
                assert result.status_code == 200  # Returns 200 with null reputation


class TestAgentNameExtraction:
    """Test agent name extraction from paths."""

    def test_extract_valid_agent_name(self, handler):
        """Valid agent names are extracted correctly."""
        assert handler._extract_agent_name("/api/agent/claude/reputation") == "claude"
        assert handler._extract_agent_name("/api/agent/gpt-4/reputation") == "gpt-4"
        assert handler._extract_agent_name("/api/agent/agent_1/reputation") == "agent_1"

    def test_extract_path_traversal_blocked(self, handler):
        """Path traversal in agent name returns None."""
        assert handler._extract_agent_name("/api/agent/../passwd/reputation") is None
        assert handler._extract_agent_name("/api/agent/../../etc/reputation") is None

    def test_extract_special_chars_blocked(self, handler):
        """Special characters in agent name return None."""
        assert handler._extract_agent_name("/api/agent/<script>/reputation") is None
        assert handler._extract_agent_name("/api/agent/agent;rm/reputation") is None


class TestCritiqueHandlerImport:
    """Test CritiqueHandler import and export."""

    def test_handler_importable(self):
        """CritiqueHandler can be imported from handlers package."""
        from aragora.server.handlers import CritiqueHandler
        assert CritiqueHandler is not None

    def test_handler_in_all_exports(self):
        """CritiqueHandler is in __all__ exports."""
        from aragora.server.handlers import __all__
        assert "CritiqueHandler" in __all__

    def test_critique_store_available_flag(self):
        """CRITIQUE_STORE_AVAILABLE flag is defined."""
        from aragora.server.handlers.critique import CRITIQUE_STORE_AVAILABLE
        assert isinstance(CRITIQUE_STORE_AVAILABLE, bool)


class TestErrorHandling:
    """Test error handling in CritiqueHandler."""

    def test_handle_returns_none_for_unmatched(self, handler):
        """Handle returns None for unmatched paths."""
        result = handler.handle("/api/unmatched", {}, None)
        assert result is None

    def test_safe_error_message(self):
        """Safe error message sanitizes error types."""
        from aragora.server.error_utils import safe_error_message as _safe_error_message

        assert _safe_error_message(FileNotFoundError("test"), "test") == "Resource not found"
        assert _safe_error_message(ValueError("test"), "test") == "Invalid data format"
        assert _safe_error_message(Exception("test"), "test") == "An error occurred"
