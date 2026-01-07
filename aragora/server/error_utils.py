"""Centralized error handling and structured error responses.

Provides consistent error message handling across the server:
- sanitize_error_text: Redacts sensitive data from error strings
- safe_error_message: Maps exceptions to user-friendly messages
- APIError: Structured error class with codes and metadata
- ErrorCode: Standard error code constants
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Import shared sanitization utilities
from aragora.utils.error_sanitizer import (
    sanitize_error_text,
    SENSITIVE_PATTERNS as _SENSITIVE_PATTERNS,  # For backwards compatibility
)


# =============================================================================
# Error Codes
# =============================================================================

class ErrorCode(str, Enum):
    """Standard error codes for structured API responses."""

    # Client errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    INVALID_FORMAT = "INVALID_FORMAT"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"

    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"

    # Domain-specific errors
    DEBATE_ERROR = "DEBATE_ERROR"
    AGENT_ERROR = "AGENT_ERROR"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"


# Map HTTP status codes to error codes
_STATUS_TO_CODE = {
    400: ErrorCode.INVALID_REQUEST,
    401: ErrorCode.UNAUTHORIZED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    409: ErrorCode.CONFLICT,
    413: ErrorCode.PAYLOAD_TOO_LARGE,
    429: ErrorCode.RATE_LIMITED,
    500: ErrorCode.INTERNAL_ERROR,
    502: ErrorCode.EXTERNAL_SERVICE_ERROR,
    503: ErrorCode.SERVICE_UNAVAILABLE,
    504: ErrorCode.TIMEOUT,
}


# =============================================================================
# APIError Class
# =============================================================================

@dataclass
class APIError(Exception):
    """
    Structured API error with code, message, and metadata.

    Provides consistent error format across all API endpoints:
    {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Invalid agent name",
            "status": 400,
            "trace_id": "abc123",
            "details": {"field": "agent"},
            "suggestion": "Use GET /api/agents for valid names"
        }
    }
    """

    code: ErrorCode
    message: str
    status: int = 400
    trace_id: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)
    suggestion: Optional[str] = None

    def __post_init__(self):
        # Initialize exception base
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        result = {
            "code": self.code.value if isinstance(self.code, ErrorCode) else self.code,
            "message": self.message,
            "status": self.status,
        }
        if self.trace_id:
            result["trace_id"] = self.trace_id
        if self.details:
            result["details"] = self.details
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result

    def to_response(self) -> dict:
        """Convert to full error response envelope."""
        return {"error": self.to_dict()}

    @classmethod
    def from_status(
        cls,
        status: int,
        message: str,
        trace_id: Optional[str] = None,
        details: Optional[dict] = None,
        suggestion: Optional[str] = None,
    ) -> "APIError":
        """Create APIError from HTTP status code."""
        code = _STATUS_TO_CODE.get(status, ErrorCode.INTERNAL_ERROR)
        return cls(
            code=code,
            message=message,
            status=status,
            trace_id=trace_id,
            details=details or {},
            suggestion=suggestion,
        )

    @classmethod
    def validation_error(
        cls,
        message: str,
        field: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> "APIError":
        """Create a validation error."""
        details = {"field": field} if field else {}
        return cls(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status=400,
            trace_id=trace_id,
            details=details,
        )

    @classmethod
    def not_found(
        cls,
        resource: str,
        resource_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> "APIError":
        """Create a not found error."""
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} '{resource_id}' not found"
        return cls(
            code=ErrorCode.NOT_FOUND,
            message=message,
            status=404,
            trace_id=trace_id,
            details={"resource": resource, "id": resource_id} if resource_id else {},
        )

    @classmethod
    def rate_limited(
        cls,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        trace_id: Optional[str] = None,
    ) -> "APIError":
        """Create a rate limit error."""
        details = {"retry_after": retry_after} if retry_after else {}
        suggestion = f"Retry after {retry_after} seconds" if retry_after else "Please try again later"
        return cls(
            code=ErrorCode.RATE_LIMITED,
            message=message,
            status=429,
            trace_id=trace_id,
            details=details,
            suggestion=suggestion,
        )

    @classmethod
    def internal_error(
        cls,
        message: str = "An internal error occurred",
        trace_id: Optional[str] = None,
    ) -> "APIError":
        """Create an internal server error."""
        return cls(
            code=ErrorCode.INTERNAL_ERROR,
            message=message,
            status=500,
            trace_id=trace_id,
            suggestion="If this persists, contact support with the trace ID",
        )


# =============================================================================
# Helper Functions
# =============================================================================

def safe_error_message(e: Exception, context: str = "") -> str:
    """Return a sanitized error message for client responses.

    Logs the full error server-side while returning a generic message to clients.
    This prevents information disclosure of internal details like file paths,
    stack traces, or sensitive configuration.

    Args:
        e: The exception that occurred
        context: Optional context string for logging (e.g., "debate creation")

    Returns:
        User-friendly error message safe to return to clients
    """
    # Log full details server-side for debugging
    logger.error(f"Error in {context}: {type(e).__name__}: {e}", exc_info=True)

    # Map common exceptions to user-friendly messages
    error_type = type(e).__name__
    if error_type in ("FileNotFoundError", "OSError"):
        return "Resource not found"
    elif error_type in ("json.JSONDecodeError", "ValueError"):
        return "Invalid data format"
    elif error_type in ("PermissionError",):
        return "Access denied"
    elif error_type in ("TimeoutError", "asyncio.TimeoutError"):
        return "Operation timed out"
    else:
        return "An error occurred"
