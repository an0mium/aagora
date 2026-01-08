"""Tests for BeliefHandler."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from aragora.server.handlers.belief import BeliefHandler


class TestBeliefHandlerRouting:
    """Tests for route matching."""

    @pytest.fixture
    def handler(self):
        """Create handler with mock context."""
        return BeliefHandler({"nomic_dir": Path("/tmp/test")})

    def test_cannot_handle_emergent_traits(self, handler):
        """Should NOT handle /api/laboratory/emergent-traits (moved to LaboratoryHandler)."""
        assert handler.can_handle("/api/laboratory/emergent-traits") is False

    def test_can_handle_cruxes(self, handler):
        """Should handle /api/belief-network/:debate_id/cruxes."""
        assert handler.can_handle("/api/belief-network/debate-123/cruxes") is True

    def test_can_handle_load_bearing_claims(self, handler):
        """Should handle /api/belief-network/:debate_id/load-bearing-claims."""
        assert handler.can_handle("/api/belief-network/debate-456/load-bearing-claims") is True

    def test_can_handle_claim_support(self, handler):
        """Should handle /api/provenance/:debate_id/claims/:claim_id/support."""
        assert handler.can_handle("/api/provenance/debate-123/claims/claim-456/support") is True

    def test_can_handle_graph_stats(self, handler):
        """Should handle /api/debate/:debate_id/graph-stats."""
        assert handler.can_handle("/api/debate/debate-123/graph-stats") is True

    def test_cannot_handle_unrelated(self, handler):
        """Should not handle unrelated routes."""
        assert handler.can_handle("/api/debates") is False
        assert handler.can_handle("/api/agents") is False
        assert handler.can_handle("/api/relationships/summary") is False

    def test_cannot_handle_partial_paths(self, handler):
        """Should not handle incomplete paths."""
        assert handler.can_handle("/api/belief-network/debate-123") is False
        assert handler.can_handle("/api/laboratory") is False


# Note: TestEmergentTraitsEndpoint moved to test_handlers_laboratory.py
# since /api/laboratory/emergent-traits is now handled by LaboratoryHandler


class TestCruxesEndpoint:
    """Tests for /api/belief-network/:debate_id/cruxes endpoint."""

    @pytest.fixture
    def handler(self):
        """Create handler with mock context."""
        return BeliefHandler({"nomic_dir": Path("/tmp/test")})

    @patch("aragora.server.handlers.belief.BELIEF_NETWORK_AVAILABLE", False)
    def test_503_when_belief_network_unavailable(self, handler):
        """Should return 503 when belief network not available."""
        result = handler.handle("/api/belief-network/debate-123/cruxes", {}, Mock())
        assert result.status_code == 503

    def test_rejects_invalid_debate_id(self, handler):
        """Should reject debate IDs with path traversal."""
        result = handler.handle("/api/belief-network/../etc/cruxes", {}, Mock())
        assert result.status_code == 400


class TestLoadBearingClaimsEndpoint:
    """Tests for /api/belief-network/:debate_id/load-bearing-claims endpoint."""

    @pytest.fixture
    def handler(self):
        """Create handler with mock context."""
        return BeliefHandler({"nomic_dir": Path("/tmp/test")})

    @patch("aragora.server.handlers.belief.BELIEF_NETWORK_AVAILABLE", False)
    def test_503_when_belief_network_unavailable(self, handler):
        """Should return 503 when belief network not available."""
        result = handler.handle("/api/belief-network/debate-123/load-bearing-claims", {}, Mock())
        assert result.status_code == 503


class TestClaimSupportEndpoint:
    """Tests for /api/provenance/:debate_id/claims/:claim_id/support endpoint."""

    @pytest.fixture
    def handler(self):
        """Create handler with mock context."""
        return BeliefHandler({"nomic_dir": Path("/tmp/test")})

    @patch("aragora.server.handlers.belief.PROVENANCE_AVAILABLE", False)
    def test_503_when_provenance_unavailable(self, handler):
        """Should return 503 when provenance not available."""
        result = handler.handle("/api/provenance/debate-123/claims/claim-456/support", {}, Mock())
        assert result.status_code == 503

    def test_rejects_invalid_claim_id(self, handler):
        """Should reject claim IDs with special characters."""
        result = handler.handle("/api/provenance/debate-123/claims/../etc/support", {}, Mock())
        assert result.status_code == 400

    def test_rejects_invalid_path_format(self, handler):
        """Should reject malformed paths."""
        result = handler.handle("/api/provenance/support", {}, Mock())
        # This path doesn't match can_handle, so returns None
        assert result is None


class TestGraphStatsEndpoint:
    """Tests for /api/debate/:debate_id/graph-stats endpoint."""

    @pytest.fixture
    def handler(self):
        """Create handler with mock context."""
        return BeliefHandler({"nomic_dir": Path("/tmp/test")})

    def test_returns_503_without_nomic_dir(self):
        """Should return 503 when nomic_dir not configured."""
        handler = BeliefHandler({"nomic_dir": None})
        result = handler.handle("/api/debate/debate-123/graph-stats", {}, Mock())
        assert result.status_code == 503
        data = json.loads(result.body)
        assert "not configured" in data["error"]


class TestDebateIdExtraction:
    """Tests for debate ID extraction and validation."""

    @pytest.fixture
    def handler(self):
        """Create handler with mock context."""
        return BeliefHandler({"nomic_dir": Path("/tmp/test")})

    def test_extracts_valid_debate_id(self, handler):
        """Should extract valid debate ID from path."""
        debate_id = handler._extract_debate_id("/api/belief-network/debate-123/cruxes", 3)
        assert debate_id == "debate-123"

    def test_extracts_id_with_underscores(self, handler):
        """Should accept IDs with underscores."""
        debate_id = handler._extract_debate_id("/api/belief-network/debate_123_abc/cruxes", 3)
        assert debate_id == "debate_123_abc"

    def test_rejects_path_traversal(self, handler):
        """Should reject path traversal attempts."""
        debate_id = handler._extract_debate_id("/api/belief-network/../etc/cruxes", 3)
        assert debate_id is None

    def test_rejects_special_characters(self, handler):
        """Should reject special characters."""
        debate_id = handler._extract_debate_id("/api/belief-network/debate;drop/cruxes", 3)
        assert debate_id is None


class TestHandlerImport:
    """Tests for handler module imports."""

    def test_handler_can_be_imported(self):
        """Should be importable from handlers package."""
        from aragora.server.handlers import BeliefHandler
        assert BeliefHandler is not None

    def test_handler_in_all(self):
        """Should be in __all__ exports."""
        from aragora.server.handlers import __all__
        assert "BeliefHandler" in __all__


# ============================================================================
# Success Path Tests
# ============================================================================

class TestCruxesSuccessPath:
    """Tests for successful cruxes endpoint calls."""

    @pytest.fixture
    def handler_with_nomic(self, tmp_path):
        """Create handler with nomic_dir configured."""
        return BeliefHandler({"nomic_dir": tmp_path})

    def test_returns_404_when_trace_not_found(self, handler_with_nomic):
        """Should return 404 when debate trace doesn't exist."""
        with patch("aragora.server.handlers.belief.BELIEF_NETWORK_AVAILABLE", True):
            result = handler_with_nomic.handle(
                "/api/belief-network/debate-123/cruxes", {}, Mock()
            )
            assert result.status_code == 404
            data = json.loads(result.body)
            assert "not found" in data["error"].lower()

    def test_returns_503_without_nomic_dir(self):
        """Should return 503 when nomic_dir not configured."""
        handler = BeliefHandler({"nomic_dir": None})
        with patch("aragora.server.handlers.belief.BELIEF_NETWORK_AVAILABLE", True):
            result = handler.handle(
                "/api/belief-network/debate-123/cruxes", {}, Mock()
            )
            assert result.status_code == 503

    def test_top_k_parameter_clamping(self, handler_with_nomic):
        """Should clamp top_k parameter to valid range."""
        with patch("aragora.server.handlers.belief.BELIEF_NETWORK_AVAILABLE", True):
            # Test with out-of-range value
            result = handler_with_nomic.handle(
                "/api/belief-network/debate-123/cruxes",
                {"top_k": "100"},  # Above max of 10
                Mock()
            )
            # Should return 404 (trace not found) not validation error
            assert result.status_code == 404


class TestLoadBearingClaimsSuccessPath:
    """Tests for successful load-bearing claims endpoint calls."""

    @pytest.fixture
    def handler_with_nomic(self, tmp_path):
        """Create handler with nomic_dir configured."""
        return BeliefHandler({"nomic_dir": tmp_path})

    def test_returns_404_when_trace_not_found(self, handler_with_nomic):
        """Should return 404 when debate trace doesn't exist."""
        with patch("aragora.server.handlers.belief.BELIEF_NETWORK_AVAILABLE", True):
            result = handler_with_nomic.handle(
                "/api/belief-network/debate-123/load-bearing-claims", {}, Mock()
            )
            assert result.status_code == 404

    def test_returns_503_without_nomic_dir(self):
        """Should return 503 when nomic_dir not configured."""
        handler = BeliefHandler({"nomic_dir": None})
        with patch("aragora.server.handlers.belief.BELIEF_NETWORK_AVAILABLE", True):
            result = handler.handle(
                "/api/belief-network/debate-123/load-bearing-claims", {}, Mock()
            )
            assert result.status_code == 503

    def test_limit_parameter(self, handler_with_nomic):
        """Should accept limit parameter."""
        with patch("aragora.server.handlers.belief.BELIEF_NETWORK_AVAILABLE", True):
            result = handler_with_nomic.handle(
                "/api/belief-network/debate-123/load-bearing-claims",
                {"limit": "10"},
                Mock()
            )
            # Returns 404 because trace doesn't exist
            assert result.status_code == 404


class TestClaimSupportSuccessPath:
    """Tests for successful claim support endpoint calls."""

    @pytest.fixture
    def handler_with_nomic(self, tmp_path):
        """Create handler with nomic_dir configured."""
        return BeliefHandler({"nomic_dir": tmp_path})

    def test_returns_message_when_no_provenance(self, handler_with_nomic):
        """Should return message when provenance file doesn't exist."""
        with patch("aragora.server.handlers.belief.PROVENANCE_AVAILABLE", True):
            result = handler_with_nomic.handle(
                "/api/provenance/debate-123/claims/claim-456/support", {}, Mock()
            )
            assert result.status_code == 200
            data = json.loads(result.body)
            assert data["support"] is None
            assert "No provenance data" in data["message"]

    def test_returns_503_without_nomic_dir(self):
        """Should return 503 when nomic_dir not configured."""
        handler = BeliefHandler({"nomic_dir": None})
        with patch("aragora.server.handlers.belief.PROVENANCE_AVAILABLE", True):
            result = handler.handle(
                "/api/provenance/debate-123/claims/claim-456/support", {}, Mock()
            )
            assert result.status_code == 503


class TestGraphStatsSuccessPath:
    """Tests for successful graph-stats endpoint calls."""

    @pytest.fixture
    def handler_with_nomic(self, tmp_path):
        """Create handler with nomic_dir configured."""
        return BeliefHandler({"nomic_dir": tmp_path})

    def test_returns_404_when_debate_not_found(self, handler_with_nomic):
        """Should return 404 when neither trace nor replay exists."""
        result = handler_with_nomic.handle(
            "/api/debate/debate-123/graph-stats", {}, Mock()
        )
        assert result.status_code == 404
        data = json.loads(result.body)
        assert "not found" in data["error"].lower()

    def test_loads_from_trace_file(self, handler_with_nomic, tmp_path):
        """Should load debate from trace file."""
        # Create traces directory and mock trace
        traces_dir = tmp_path / "traces"
        traces_dir.mkdir()
        trace_file = traces_dir / "debate-123.json"

        mock_trace = MagicMock()
        mock_result = MagicMock()
        mock_result.task = "Test task"
        mock_result.messages = []
        mock_result.critiques = []
        mock_trace.to_debate_result.return_value = mock_result

        mock_cartographer = MagicMock()
        mock_cartographer.get_statistics.return_value = {
            "total_nodes": 5,
            "total_edges": 3,
        }

        with patch("aragora.debate.traces.DebateTrace.load", return_value=mock_trace):
            with patch("aragora.visualization.mapper.ArgumentCartographer", return_value=mock_cartographer):
                trace_file.write_text("{}")  # Create empty file
                result = handler_with_nomic.handle(
                    "/api/debate/debate-123/graph-stats", {}, Mock()
                )

        assert result.status_code == 200
        data = json.loads(result.body)
        assert "total_nodes" in data

    def test_loads_from_replay_file(self, handler_with_nomic, tmp_path):
        """Should fallback to replay file when trace not found."""
        # Create replays directory and mock replay
        replays_dir = tmp_path / "replays" / "debate-123"
        replays_dir.mkdir(parents=True)
        events_file = replays_dir / "events.jsonl"
        events_file.write_text('{"type": "agent_message", "agent": "claude", "round": 1, "data": {"content": "test", "role": "proposer"}}\n')

        mock_cartographer = MagicMock()
        mock_cartographer.get_statistics.return_value = {
            "total_nodes": 1,
            "total_edges": 0,
        }

        with patch("aragora.visualization.mapper.ArgumentCartographer", return_value=mock_cartographer):
            result = handler_with_nomic.handle(
                "/api/debate/debate-123/graph-stats", {}, Mock()
            )

        assert result.status_code == 200
        data = json.loads(result.body)
        assert "total_nodes" in data

    def test_handles_critique_events(self, handler_with_nomic, tmp_path):
        """Should process critique events from replay."""
        replays_dir = tmp_path / "replays" / "debate-456"
        replays_dir.mkdir(parents=True)
        events_file = replays_dir / "events.jsonl"
        events_file.write_text(
            '{"type": "critique", "agent": "gpt4", "round": 1, "data": {"target": "claude", "severity": 0.7, "content": "needs more detail"}}\n'
        )

        mock_cartographer = MagicMock()
        mock_cartographer.get_statistics.return_value = {"stats": "data"}

        with patch("aragora.visualization.mapper.ArgumentCartographer", return_value=mock_cartographer):
            result = handler_with_nomic.handle(
                "/api/debate/debate-456/graph-stats", {}, Mock()
            )

        assert result.status_code == 200
        mock_cartographer.update_from_critique.assert_called()


class TestEmergentTraitsMethod:
    """Tests for _get_emergent_traits method."""

    @pytest.fixture
    def handler(self, tmp_path):
        """Create handler with nomic_dir."""
        return BeliefHandler({"nomic_dir": tmp_path, "persona_manager": Mock()})

    def test_returns_503_when_laboratory_unavailable(self, handler):
        """Should return 503 when laboratory not available."""
        with patch("aragora.server.handlers.belief.LABORATORY_AVAILABLE", False):
            result = handler._get_emergent_traits(None, None, 0.5, 10)
            assert result.status_code == 503

    def test_filters_by_confidence(self, handler, tmp_path):
        """Should filter traits by min_confidence."""
        mock_lab = MagicMock()
        mock_trait_high = MagicMock()
        mock_trait_high.confidence = 0.9
        mock_trait_high.agent_name = "claude"
        mock_trait_high.trait_name = "analytical"
        mock_trait_high.domain = "coding"
        mock_trait_high.evidence = []
        mock_trait_high.detected_at = "2024-01-01"

        mock_trait_low = MagicMock()
        mock_trait_low.confidence = 0.3

        mock_lab.detect_emergent_traits.return_value = [mock_trait_high, mock_trait_low]

        with patch("aragora.server.handlers.belief.LABORATORY_AVAILABLE", True):
            with patch("aragora.server.handlers.belief.PersonaLaboratory", return_value=mock_lab):
                result = handler._get_emergent_traits(tmp_path, Mock(), 0.5, 10)

        assert result.status_code == 200
        data = json.loads(result.body)
        assert data["count"] == 1
        assert data["emergent_traits"][0]["agent"] == "claude"

    def test_respects_limit(self, handler, tmp_path):
        """Should respect limit parameter."""
        mock_lab = MagicMock()
        traits = []
        for i in range(5):
            t = MagicMock()
            t.confidence = 0.9
            t.agent_name = f"agent{i}"
            t.trait_name = "trait"
            t.domain = "domain"
            t.evidence = []
            t.detected_at = "2024-01-01"
            traits.append(t)

        mock_lab.detect_emergent_traits.return_value = traits

        with patch("aragora.server.handlers.belief.LABORATORY_AVAILABLE", True):
            with patch("aragora.server.handlers.belief.PersonaLaboratory", return_value=mock_lab):
                result = handler._get_emergent_traits(tmp_path, Mock(), 0.5, 2)

        data = json.loads(result.body)
        assert data["count"] == 2


# Note: TestParameterValidation for emergent-traits moved to test_handlers_laboratory.py
# since /api/laboratory/emergent-traits is now handled by LaboratoryHandler
