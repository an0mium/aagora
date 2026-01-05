"""
Formal verification endpoint handlers.

Endpoints:
- GET /api/verification/status - Get status of formal verification backends
"""

from typing import Optional
from .base import BaseHandler, HandlerResult, json_response, error_response

# Try to import formal verification
try:
    from aragora.debate.verification import get_formal_verification_manager
    FORMAL_VERIFICATION_AVAILABLE = True
except ImportError:
    FORMAL_VERIFICATION_AVAILABLE = False
    get_formal_verification_manager = None


class VerificationHandler(BaseHandler):
    """Handler for formal verification endpoints."""

    ROUTES = [
        "/api/verification/status",
    ]

    def can_handle(self, path: str) -> bool:
        """Check if this handler can process the given path."""
        return path in self.ROUTES

    def handle(self, path: str, query_params: dict, handler) -> Optional[HandlerResult]:
        """Route verification requests to appropriate methods."""
        if path == "/api/verification/status":
            return self._get_verification_status()

        return None

    def _get_verification_status(self) -> HandlerResult:
        """Get status of formal verification backends.

        Returns availability of Z3 and Lean backends.
        """
        if not FORMAL_VERIFICATION_AVAILABLE:
            return json_response({
                "available": False,
                "hint": "Install z3-solver: pip install z3-solver",
                "backends": [],
            })

        try:
            manager = get_formal_verification_manager()
            status = manager.status_report()
            return json_response({
                "available": status.get("any_available", False),
                "backends": status.get("backends", []),
            })
        except Exception as e:
            return error_response(f"Failed to get verification status: {e}", 500)
