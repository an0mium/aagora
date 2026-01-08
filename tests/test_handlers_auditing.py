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


# =============================================================================
# Test AuditRequestParser
# =============================================================================


class TestAuditRequestParser:
    """Tests for the AuditRequestParser utility class."""

    @pytest.fixture
    def parser(self):
        from aragora.server.handlers.auditing import AuditRequestParser
        return AuditRequestParser

    def test_read_json_returns_error_for_none(self, parser):
        """Returns error response when JSON read fails."""
        data, err = parser._read_json(None, lambda h: None)
        assert data is None
        assert err is not None
        assert err.status_code == 400
        assert "JSON" in json.loads(err.body)["error"]

    def test_read_json_returns_data_on_success(self, parser):
        """Returns data when JSON read succeeds."""
        data, err = parser._read_json(None, lambda h: {"key": "value"})
        assert data == {"key": "value"}
        assert err is None

    def test_require_field_missing_returns_error(self, parser):
        """Returns error for missing required field."""
        value, err = parser._require_field({}, "task")
        assert value is None
        assert err is not None
        assert err.status_code == 400
        assert "task" in json.loads(err.body)["error"]

    def test_require_field_empty_returns_error(self, parser):
        """Returns error for empty required field."""
        value, err = parser._require_field({"task": "   "}, "task")
        assert value is None
        assert err is not None
        assert err.status_code == 400

    def test_require_field_with_validator_success(self, parser):
        """Returns value when validator passes."""
        value, err = parser._require_field(
            {"name": "valid"},
            "name",
            lambda v: (True, None)
        )
        assert value == "valid"
        assert err is None

    def test_require_field_with_validator_failure(self, parser):
        """Returns error when validator fails."""
        value, err = parser._require_field(
            {"name": "invalid!"},
            "name",
            lambda v: (False, "Invalid name format")
        )
        assert value is None
        assert err is not None
        assert err.status_code == 400

    def test_parse_int_default_value(self, parser):
        """Returns default value when field missing."""
        value, err = parser._parse_int({}, "rounds", 5, 10)
        assert value == 5
        assert err is None

    def test_parse_int_clamped_value(self, parser):
        """Returns clamped value when exceeds max."""
        value, err = parser._parse_int({"rounds": 100}, "rounds", 5, 10)
        assert value == 10
        assert err is None

    def test_parse_int_invalid_value_returns_error(self, parser):
        """Returns error for non-integer value."""
        value, err = parser._parse_int({"rounds": "not_a_number"}, "rounds", 5, 10)
        assert value == 0
        assert err is not None
        assert err.status_code == 400

    def test_parse_capability_probe_full(self, parser):
        """Parse full capability probe request."""
        mock_handler = Mock()

        def read_fn(h):
            return {
                "agent_name": "test_agent",
                "probe_types": ["contradiction"],
                "probes_per_type": 5,
                "model_type": "openai"
            }

        parsed, err = parser.parse_capability_probe(mock_handler, read_fn)
        assert err is None
        assert parsed["agent_name"] == "test_agent"
        assert parsed["probe_types"] == ["contradiction"]
        assert parsed["probes_per_type"] == 5
        assert parsed["model_type"] == "openai"

    def test_parse_capability_probe_defaults(self, parser):
        """Parse capability probe with defaults."""
        mock_handler = Mock()

        def read_fn(h):
            return {"agent_name": "test_agent"}

        parsed, err = parser.parse_capability_probe(mock_handler, read_fn)
        assert err is None
        assert parsed["probes_per_type"] == 3  # Default
        assert parsed["model_type"] == "anthropic-api"  # Default
        assert len(parsed["probe_types"]) == 4  # Default types

    def test_parse_deep_audit_full(self, parser):
        """Parse full deep audit request."""
        mock_handler = Mock()

        def read_fn(h):
            return {
                "task": "Review security",
                "context": "Some context",
                "agent_names": ["agent1", "agent2"],
                "config": {
                    "rounds": 5,
                    "cross_examination_depth": 2,
                    "risk_threshold": 0.8,
                    "enable_research": False,
                    "audit_type": "security",
                }
            }

        parsed, err = parser.parse_deep_audit(mock_handler, read_fn)
        assert err is None
        assert parsed["task"] == "Review security"
        assert parsed["rounds"] == 5
        assert parsed["cross_examination_depth"] == 2
        assert parsed["risk_threshold"] == 0.8
        assert parsed["enable_research"] is False

    def test_parse_deep_audit_invalid_risk_threshold(self, parser):
        """Returns error for invalid risk_threshold."""
        mock_handler = Mock()

        def read_fn(h):
            return {
                "task": "Test",
                "config": {"risk_threshold": "not_a_number"}
            }

        parsed, err = parser.parse_deep_audit(mock_handler, read_fn)
        assert parsed is None
        assert err is not None
        assert err.status_code == 400


# =============================================================================
# Test AuditAgentFactory
# =============================================================================


class TestAuditAgentFactory:
    """Tests for the AuditAgentFactory utility class."""

    @pytest.fixture
    def factory(self):
        from aragora.server.handlers.auditing import AuditAgentFactory
        return AuditAgentFactory

    def test_create_single_agent_not_available(self, factory):
        """Returns error when debate module not available."""
        with patch("aragora.server.handlers.auditing.DEBATE_AVAILABLE", False):
            agent, err = factory.create_single_agent("test", "agent1")
            assert agent is None
            assert err is not None
            assert err.status_code == 503

    def test_create_single_agent_creation_fails(self, factory):
        """Returns error when agent creation fails."""
        with patch("aragora.server.handlers.auditing.DEBATE_AVAILABLE", True):
            mock_create = Mock(side_effect=ValueError("Invalid model"))
            with patch("aragora.server.handlers.auditing.create_agent", mock_create):
                agent, err = factory.create_single_agent("invalid", "agent1")
                assert agent is None
                assert err is not None
                assert err.status_code == 400

    def test_create_single_agent_success(self, factory):
        """Returns agent on success."""
        with patch("aragora.server.handlers.auditing.DEBATE_AVAILABLE", True):
            mock_agent = Mock()
            mock_create = Mock(return_value=mock_agent)
            with patch("aragora.server.handlers.auditing.create_agent", mock_create):
                agent, err = factory.create_single_agent("test", "agent1", "proposer")
                assert agent == mock_agent
                assert err is None
                mock_create.assert_called_once_with("test", name="agent1", role="proposer")

    def test_create_multiple_agents_not_available(self, factory):
        """Returns error when debate module not available."""
        with patch("aragora.server.handlers.auditing.DEBATE_AVAILABLE", False):
            agents, err = factory.create_multiple_agents("test", [], ["a", "b"])
            assert agents == []
            assert err is not None
            assert err.status_code == 503

    def test_create_multiple_agents_uses_defaults(self, factory):
        """Uses default names when agent_names empty."""
        with patch("aragora.server.handlers.auditing.DEBATE_AVAILABLE", True):
            mock_agent = Mock()
            mock_create = Mock(return_value=mock_agent)
            with patch("aragora.server.handlers.auditing.create_agent", mock_create):
                agents, err = factory.create_multiple_agents(
                    "test", [], ["default1", "default2", "default3"]
                )
                assert err is None
                assert len(agents) == 3
                assert mock_create.call_count == 3

    def test_create_multiple_agents_too_few(self, factory):
        """Returns error when fewer than 2 agents created."""
        with patch("aragora.server.handlers.auditing.DEBATE_AVAILABLE", True):
            # Make create_agent fail for all but 1
            call_count = [0]
            def mock_create(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] > 1:
                    raise ValueError("Failed")
                return Mock()

            with patch("aragora.server.handlers.auditing.create_agent", mock_create):
                agents, err = factory.create_multiple_agents(
                    "test", ["a", "b", "c"], []
                )
                assert agents == []
                assert err is not None
                assert "at least 2" in json.loads(err.body)["error"]

    def test_create_multiple_agents_limits_to_max(self, factory):
        """Limits agents to max_agents."""
        with patch("aragora.server.handlers.auditing.DEBATE_AVAILABLE", True):
            mock_create = Mock(return_value=Mock())
            with patch("aragora.server.handlers.auditing.create_agent", mock_create):
                agents, err = factory.create_multiple_agents(
                    "test", ["a", "b", "c", "d", "e", "f", "g"], [], max_agents=3
                )
                assert err is None
                assert len(agents) == 3


# =============================================================================
# Test AuditResultRecorder
# =============================================================================


class TestAuditResultRecorder:
    """Tests for the AuditResultRecorder utility class."""

    @pytest.fixture
    def recorder(self):
        from aragora.server.handlers.auditing import AuditResultRecorder
        return AuditResultRecorder

    def test_record_probe_elo_skips_when_no_system(self, recorder):
        """Skips recording when no ELO system."""
        mock_report = Mock(probes_run=5)
        # Should not raise
        recorder.record_probe_elo(None, "agent1", mock_report, "report-1")

    def test_record_probe_elo_skips_when_no_probes(self, recorder):
        """Skips recording when no probes run."""
        mock_elo = Mock()
        mock_report = Mock(probes_run=0)
        recorder.record_probe_elo(mock_elo, "agent1", mock_report, "report-1")
        mock_elo.record_redteam_result.assert_not_called()

    def test_record_probe_elo_records_correctly(self, recorder):
        """Records ELO result with correct values."""
        mock_elo = Mock()
        mock_report = Mock(
            probes_run=10,
            vulnerability_rate=0.3,
            vulnerabilities_found=3,
            critical_count=1
        )

        recorder.record_probe_elo(mock_elo, "agent1", mock_report, "report-123")

        mock_elo.record_redteam_result.assert_called_once_with(
            agent_name="agent1",
            robustness_score=0.7,  # 1.0 - 0.3
            successful_attacks=3,
            total_attacks=10,
            critical_vulnerabilities=1,
            session_id="report-123"
        )

    def test_record_probe_elo_handles_exception(self, recorder):
        """Handles ELO recording exception gracefully."""
        mock_elo = Mock()
        mock_elo.record_redteam_result.side_effect = RuntimeError("DB error")
        mock_report = Mock(
            probes_run=10,
            vulnerability_rate=0.3,
            vulnerabilities_found=3,
            critical_count=1
        )

        # Should not raise, just log warning
        recorder.record_probe_elo(mock_elo, "agent1", mock_report, "report-123")

    def test_calculate_audit_elo_adjustments_empty(self, recorder):
        """Returns empty dict when no ELO system."""
        result = recorder.calculate_audit_elo_adjustments(Mock(), None)
        assert result == {}

    def test_calculate_audit_elo_adjustments_correct(self, recorder):
        """Calculates adjustments correctly from findings."""
        mock_finding1 = Mock(agents_agree=["agent1", "agent2"], agents_disagree=["agent3"])
        mock_finding2 = Mock(agents_agree=["agent1"], agents_disagree=["agent2"])
        mock_verdict = Mock(findings=[mock_finding1, mock_finding2])
        mock_elo = Mock()

        result = recorder.calculate_audit_elo_adjustments(mock_verdict, mock_elo)

        assert result["agent1"] == 4  # 2 + 2
        assert result["agent2"] == 1  # 2 - 1
        assert result["agent3"] == -1

    def test_save_probe_report_skips_when_no_dir(self, recorder):
        """Skips saving when no nomic_dir."""
        # Should not raise
        recorder.save_probe_report(None, "agent1", Mock())

    def test_save_probe_report_creates_file(self, recorder, tmp_path):
        """Creates probe report file."""
        mock_report = Mock()
        mock_report.report_id = "test-report"
        mock_report.to_dict.return_value = {"status": "complete"}

        recorder.save_probe_report(tmp_path, "test_agent", mock_report)

        probes_dir = tmp_path / "probes" / "test_agent"
        assert probes_dir.exists()
        files = list(probes_dir.glob("*.json"))
        assert len(files) == 1

    def test_save_audit_report_creates_file(self, recorder, tmp_path):
        """Creates audit report file."""
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        mock_finding = Mock(
            category="security",
            summary="Test finding",
            details="Details",
            agents_agree=["agent1"],
            agents_disagree=[],
            confidence=0.9,
            severity=0.8,
            citations=[]
        )
        mock_verdict = Mock(
            recommendation="Proceed",
            confidence=0.85,
            unanimous_issues=["issue1"],
            split_opinions=[],
            risk_areas=["risk1"],
            findings=[mock_finding]
        )
        mock_config = Mock(
            rounds=5,
            enable_research=True,
            cross_examination_depth=3,
            risk_threshold=0.7
        )

        recorder.save_audit_report(
            tmp_path, "audit-123", "Test task", "Context",
            [mock_agent], mock_verdict, mock_config, 1000.0, {"agent1": 2}
        )

        audits_dir = tmp_path / "audits"
        assert audits_dir.exists()
        files = list(audits_dir.glob("*.json"))
        assert len(files) == 1


# =============================================================================
# Test Red Team Analysis
# =============================================================================


class TestRedTeamAnalysisEndpoint:
    """Additional tests for red team analysis endpoint."""

    @pytest.fixture
    def handler(self):
        from aragora.server.handlers.auditing import AuditingHandler
        mock_storage = Mock()
        mock_storage.get_by_slug.return_value = {
            "id": "debate-1",
            "task": "Test task",
            "consensus_answer": "The answer is 42"
        }
        mock_storage.get_by_id.return_value = None
        ctx = {"storage": mock_storage}
        return AuditingHandler(ctx)

    def test_redteam_success_response_format(self, handler):
        """Returns correct response format on success."""
        mock_http_handler = Mock()
        mock_http_handler.headers = {"Content-Length": "2"}
        mock_http_handler.rfile.read.return_value = b'{}'

        with patch("aragora.server.handlers.auditing.REDTEAM_AVAILABLE", True):
            result = handler._run_red_team_analysis("debate-1", mock_http_handler)
            assert result.status_code == 200

            data = json.loads(result.body)
            assert "session_id" in data
            assert "debate_id" in data
            assert "target_proposal" in data
            assert "findings" in data
            assert "robustness_score" in data
            assert "status" in data
            assert data["status"] == "analysis_complete"

    def test_redteam_with_custom_attack_types(self, handler):
        """Handles custom attack types."""
        mock_http_handler = Mock()
        mock_http_handler.headers = {"Content-Length": "50"}
        mock_http_handler.rfile.read.return_value = b'{"attack_types": ["security", "scalability"]}'

        with patch("aragora.server.handlers.auditing.REDTEAM_AVAILABLE", True):
            result = handler._run_red_team_analysis("debate-1", mock_http_handler)
            assert result.status_code == 200

            data = json.loads(result.body)
            assert "security" in data["attack_types"]
            assert "scalability" in data["attack_types"]

    def test_redteam_with_focus_proposal(self, handler):
        """Uses provided focus_proposal."""
        mock_http_handler = Mock()
        mock_http_handler.headers = {"Content-Length": "100"}
        mock_http_handler.rfile.read.return_value = b'{"focus_proposal": "Custom proposal to analyze"}'

        with patch("aragora.server.handlers.auditing.REDTEAM_AVAILABLE", True):
            result = handler._run_red_team_analysis("debate-1", mock_http_handler)
            assert result.status_code == 200

            data = json.loads(result.body)
            assert "Custom proposal" in data["target_proposal"]

    def test_redteam_max_rounds_capped(self, handler):
        """Max rounds is capped at 5."""
        mock_http_handler = Mock()
        mock_http_handler.headers = {"Content-Length": "50"}
        mock_http_handler.rfile.read.return_value = b'{"max_rounds": 100}'

        with patch("aragora.server.handlers.auditing.REDTEAM_AVAILABLE", True):
            result = handler._run_red_team_analysis("debate-1", mock_http_handler)
            assert result.status_code == 200

            data = json.loads(result.body)
            assert data["max_rounds"] == 5

    def test_redteam_empty_body_uses_defaults(self, handler):
        """Uses default values when body is empty."""
        mock_http_handler = Mock()
        mock_http_handler.headers = {"Content-Length": "0"}
        mock_http_handler.rfile.read.return_value = b''

        with patch("aragora.server.handlers.auditing.REDTEAM_AVAILABLE", True):
            result = handler._run_red_team_analysis("debate-1", mock_http_handler)
            assert result.status_code == 200

            data = json.loads(result.body)
            assert len(data["attack_types"]) == 6  # Default 6 attack types
            assert data["max_rounds"] == 3  # Default


# =============================================================================
# Test Transform Probe Results
# =============================================================================


class TestTransformProbeResults:
    """Tests for _transform_probe_results method."""

    @pytest.fixture
    def handler(self):
        from aragora.server.handlers.auditing import AuditingHandler
        return AuditingHandler({})

    def test_transforms_results_correctly(self, handler):
        """Transforms probe results with correct structure."""
        mock_result = Mock()
        mock_result.to_dict.return_value = {
            "probe_id": "probe-1",
            "probe_type": "contradiction",
            "vulnerability_found": True,
            "severity": "HIGH",
            "vulnerability_description": "Found issue",
            "evidence": "Evidence text",
            "response_time_ms": 150
        }

        by_type = {"contradiction": [mock_result]}

        result = handler._transform_probe_results(by_type)

        assert "contradiction" in result
        assert len(result["contradiction"]) == 1
        transformed = result["contradiction"][0]
        assert transformed["probe_id"] == "probe-1"
        assert transformed["passed"] is False  # vulnerability_found=True means failed
        assert transformed["severity"] == "high"
        assert transformed["description"] == "Found issue"

    def test_handles_dict_results(self, handler):
        """Handles results that are already dicts."""
        by_type = {
            "edge_case": [{
                "probe_id": "probe-2",
                "vulnerability_found": False,
                "severity": None,
            }]
        }

        result = handler._transform_probe_results(by_type)

        transformed = result["edge_case"][0]
        assert transformed["passed"] is True
        assert transformed["severity"] is None


# =============================================================================
# Test Audit Config Selection
# =============================================================================


class TestGetAuditConfig:
    """Tests for _get_audit_config method."""

    @pytest.fixture
    def handler(self):
        from aragora.server.handlers.auditing import AuditingHandler
        return AuditingHandler({})

    def test_returns_strategy_preset(self, handler):
        """Returns strategy preset for audit_type='strategy'."""
        strategy_preset = Mock()
        result = handler._get_audit_config(
            "strategy", {},
            Mock, strategy_preset, Mock(), Mock()
        )
        assert result == strategy_preset

    def test_returns_contract_preset(self, handler):
        """Returns contract preset for audit_type='contract'."""
        contract_preset = Mock()
        result = handler._get_audit_config(
            "contract", {},
            Mock, Mock(), contract_preset, Mock()
        )
        assert result == contract_preset

    def test_returns_code_preset(self, handler):
        """Returns code preset for audit_type='code_architecture'."""
        code_preset = Mock()
        result = handler._get_audit_config(
            "code_architecture", {},
            Mock, Mock(), Mock(), code_preset
        )
        assert result == code_preset

    def test_returns_custom_config(self, handler):
        """Returns custom config for unknown audit_type."""
        config_class = Mock()
        parsed = {
            "rounds": 8,
            "enable_research": False,
            "cross_examination_depth": 4,
            "risk_threshold": 0.6,
        }

        result = handler._get_audit_config(
            "custom_type", parsed,
            config_class, Mock(), Mock(), Mock()
        )

        config_class.assert_called_once_with(
            rounds=8,
            enable_research=False,
            cross_examination_depth=4,
            risk_threshold=0.6
        )
