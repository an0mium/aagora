"""Tests for the VerificationHandler class."""

import json
import pytest
from unittest.mock import Mock, patch


class TestVerificationHandlerRouting:
    """Test route matching for VerificationHandler."""

    @pytest.fixture
    def handler(self):
        from aragora.server.handlers.verification import VerificationHandler
        ctx = {}
        return VerificationHandler(ctx)

    def test_can_handle_verification_status(self, handler):
        assert handler.can_handle("/api/verification/status") is True

    def test_cannot_handle_unknown_route(self, handler):
        assert handler.can_handle("/api/other") is False
        assert handler.can_handle("/api/verification/verify") is False


class TestVerificationStatusEndpoint:
    """Test /api/verification/status endpoint."""

    @pytest.fixture
    def handler(self):
        from aragora.server.handlers.verification import VerificationHandler
        ctx = {}
        return VerificationHandler(ctx)

    def test_status_when_unavailable(self, handler):
        """Returns unavailable status when formal verification not installed."""
        with patch("aragora.server.handlers.verification.FORMAL_VERIFICATION_AVAILABLE", False):
            result = handler.handle("/api/verification/status", {}, None)
            assert result.status_code == 200
            data = json.loads(result.body)
            assert data["available"] is False
            assert "hint" in data
            assert data["backends"] == []

    def test_status_when_available(self, handler):
        """Returns status from verification manager when available."""
        mock_manager = Mock()
        mock_manager.status_report.return_value = {
            "any_available": True,
            "backends": [
                {"name": "z3", "available": True},
                {"name": "lean", "available": False},
            ]
        }

        with patch("aragora.server.handlers.verification.FORMAL_VERIFICATION_AVAILABLE", True):
            with patch("aragora.server.handlers.verification.get_formal_verification_manager", return_value=mock_manager):
                result = handler.handle("/api/verification/status", {}, None)
                assert result.status_code == 200
                data = json.loads(result.body)
                assert data["available"] is True
                assert len(data["backends"]) == 2

    def test_status_handles_exception(self, handler):
        """Returns error when exception occurs."""
        def raise_error():
            raise RuntimeError("Backend error")

        with patch("aragora.server.handlers.verification.FORMAL_VERIFICATION_AVAILABLE", True):
            with patch("aragora.server.handlers.verification.get_formal_verification_manager", side_effect=raise_error):
                result = handler.handle("/api/verification/status", {}, None)
                assert result.status_code == 500
                data = json.loads(result.body)
                assert "error" in data


class TestVerificationHandlerImport:
    """Test VerificationHandler import and export."""

    def test_handler_importable(self):
        """VerificationHandler can be imported from handlers package."""
        from aragora.server.handlers import VerificationHandler
        assert VerificationHandler is not None

    def test_handler_in_all_exports(self):
        """VerificationHandler is in __all__ exports."""
        from aragora.server.handlers import __all__
        assert "VerificationHandler" in __all__
