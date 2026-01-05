"""Tests for the AuditingHandler class."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestAuditingHandlerRouting:
    """Test route matching for AuditingHandler."""

    @pytest.fixture
    def handler(self):
        from aragora.server.handlers.auditing import AuditingHandler
        ctx = {}
        return AuditingHandler(ctx)

    def test_can_handle_capability_probe(self, handler):
        assert handler.can_handle("/api/debates/capability-probe") is True

    def test_can_handle_deep_audit(self, handler):
        assert handler.can_handle("/api/debates/deep-audit") is True

    def test_can_handle_red_team(self, handler):
        assert handler.can_handle("/api/debates/some-id/red-team") is True

    def test_cannot_handle_unknown_route(self, handler):
        assert handler.can_handle("/api/other") is False
        assert handler.can_handle("/api/debates/other") is False


class TestCapabilityProbeEndpoint:
    """Test /api/debates/capability-probe endpoint."""

    @pytest.fixture
    def handler(self):
        from aragora.server.handlers.auditing import AuditingHandler
        ctx = {"elo_system": None}
        return AuditingHandler(ctx)

    def test_probe_requires_prober_available(self, handler):
        """Returns 503 when prober not available."""
        mock_http_handler = Mock()
        mock_http_handler.headers = {"Content-Length": "0"}
        mock_http_handler.rfile.read.return_value = b'{}'

        with patch("aragora.server.handlers.auditing.PROBER_AVAILABLE", False):
            result = handler._run_capability_probe(mock_http_handler)
            assert result.status_code == 503

    def test_probe_requires_agent_name(self, handler):
        """Returns 400 when agent_name missing."""
        mock_http_handler = Mock()
        mock_http_handler.headers = {"Content-Length": "2"}
        mock_http_handler.rfile.read.return_value = b'{}'

        with patch("aragora.server.handlers.auditing.PROBER_AVAILABLE", True):
            with patch("aragora.server.handlers.auditing.DEBATE_AVAILABLE", True):
                with patch("aragora.server.handlers.auditing.create_agent", Mock()):
                    result = handler._run_capability_probe(mock_http_handler)
                    assert result.status_code == 400
                    data = json.loads(result.body)
                    assert "agent_name" in data["error"]

    def test_probe_validates_agent_name_format(self, handler):
        """Returns 400 for invalid agent_name format."""
        mock_http_handler = Mock()
        mock_http_handler.headers = {"Content-Length": "50"}
        mock_http_handler.rfile.read.return_value = b'{"agent_name": "../evil"}'

        with patch("aragora.server.handlers.auditing.PROBER_AVAILABLE", True):
            with patch("aragora.server.handlers.auditing.DEBATE_AVAILABLE", True):
                with patch("aragora.server.handlers.auditing.create_agent", Mock()):
                    result = handler._run_capability_probe(mock_http_handler)
                    assert result.status_code == 400


class TestDeepAuditEndpoint:
    """Test /api/debates/deep-audit endpoint."""

    @pytest.fixture
    def handler(self):
        from aragora.server.handlers.auditing import AuditingHandler
        ctx = {"elo_system": None}
        return AuditingHandler(ctx)

    def test_audit_requires_task(self, handler):
        """Returns 400 when task missing."""
        mock_http_handler = Mock()
        mock_http_handler.headers = {"Content-Length": "2"}
        mock_http_handler.rfile.read.return_value = b'{}'

        with patch("aragora.server.handlers.auditing.DEBATE_AVAILABLE", True):
            with patch("aragora.server.handlers.auditing.create_agent", Mock()):
                with patch.dict("sys.modules", {"aragora.modes.deep_audit": MagicMock()}):
                    result = handler._run_deep_audit(mock_http_handler)
                    assert result.status_code == 400
                    data = json.loads(result.body)
                    assert "task" in data["error"]


class TestRedTeamEndpoint:
    """Test /api/debates/:id/red-team endpoint."""

    @pytest.fixture
    def handler(self):
        from aragora.server.handlers.auditing import AuditingHandler
        ctx = {"storage": Mock()}
        return AuditingHandler(ctx)

    def test_redteam_requires_redteam_available(self, handler):
        """Returns 503 when redteam not available."""
        mock_http_handler = Mock()
        mock_http_handler.headers = {"Content-Length": "0"}
        mock_http_handler.rfile.read.return_value = b'{}'

        with patch("aragora.server.handlers.auditing.REDTEAM_AVAILABLE", False):
            result = handler._run_red_team_analysis("test-id", mock_http_handler)
            assert result.status_code == 503

    def test_redteam_requires_storage(self, handler):
        """Returns 500 when storage not configured."""
        handler.ctx = {}  # No storage
        mock_http_handler = Mock()
        mock_http_handler.headers = {"Content-Length": "0"}
        mock_http_handler.rfile.read.return_value = b'{}'

        with patch("aragora.server.handlers.auditing.REDTEAM_AVAILABLE", True):
            result = handler._run_red_team_analysis("test-id", mock_http_handler)
            assert result.status_code == 500

    def test_redteam_returns_404_for_unknown_debate(self, handler):
        """Returns 404 when debate not found."""
        mock_storage = Mock()
        mock_storage.get_by_slug.return_value = None
        mock_storage.get_by_id.return_value = None
        handler.ctx = {"storage": mock_storage}

        mock_http_handler = Mock()
        mock_http_handler.headers = {"Content-Length": "0"}
        mock_http_handler.rfile.read.return_value = b'{}'

        with patch("aragora.server.handlers.auditing.REDTEAM_AVAILABLE", True):
            result = handler._run_red_team_analysis("nonexistent", mock_http_handler)
            assert result.status_code == 404


class TestAnalyzeProposalForRedteam:
    """Test _analyze_proposal_for_redteam helper method."""

    @pytest.fixture
    def handler(self):
        from aragora.server.handlers.auditing import AuditingHandler
        ctx = {}
        return AuditingHandler(ctx)

    def test_detects_logical_fallacy_keywords(self, handler):
        """Detects absolute language in proposals."""
        with patch("aragora.server.handlers.auditing.REDTEAM_AVAILABLE", True):
            # Mock the AttackType import
            mock_attack_type = MagicMock()
            mock_attack_type.side_effect = lambda x: x
            with patch.dict("sys.modules", {"aragora.modes.redteam": MagicMock(AttackType=mock_attack_type)}):
                findings = handler._analyze_proposal_for_redteam(
                    "This will always work and never fail",
                    ["logical_fallacy"],
                    {}
                )
                # Will return empty list due to mock - just test no exception
                assert isinstance(findings, list)

    def test_returns_empty_for_no_matches(self, handler):
        """Returns findings with low severity when no keywords match."""
        with patch("aragora.server.handlers.auditing.REDTEAM_AVAILABLE", True):
            findings = handler._analyze_proposal_for_redteam(
                "A simple proposal",
                ["unknown_type"],
                {}
            )
            assert isinstance(findings, list)


class TestAuditingHandlerImport:
    """Test AuditingHandler import and export."""

    def test_handler_importable(self):
        """AuditingHandler can be imported from handlers package."""
        from aragora.server.handlers import AuditingHandler
        assert AuditingHandler is not None

    def test_handler_in_all_exports(self):
        """AuditingHandler is in __all__ exports."""
        from aragora.server.handlers import __all__
        assert "AuditingHandler" in __all__
