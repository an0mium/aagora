"""
Standardized error handling for agent operations.

This module re-exports from aragora.agents.errors package for backward compatibility.

For new code, prefer importing directly from the package:
    from aragora.agents.errors import AgentError, handle_agent_errors
    from aragora.agents.errors.exceptions import AgentTimeoutError
    from aragora.agents.errors.classifier import ErrorClassifier
    from aragora.agents.errors.decorators import with_error_handling
"""

# Explicit re-exports from the errors package for backward compatibility
# (Avoid wildcard imports for better IDE analysis and explicit dependencies)
from aragora.agents.errors import (  # noqa: F401
    # Type variable
    T,
    # Exceptions
    AgentError,
    AgentConnectionError,
    AgentTimeoutError,
    AgentRateLimitError,
    AgentAPIError,
    AgentResponseError,
    AgentStreamError,
    AgentCircuitOpenError,
    CLIAgentError,
    CLIParseError,
    CLITimeoutError,
    CLISubprocessError,
    CLINotFoundError,
    # Patterns
    RATE_LIMIT_PATTERNS,
    NETWORK_ERROR_PATTERNS,
    CLI_ERROR_PATTERNS,
    ALL_FALLBACK_PATTERNS,
    # Dataclasses
    ErrorContext,
    ErrorAction,
    # Classifier
    ErrorClassifier,
    classify_cli_error,
    # Retry calculation
    calculate_retry_delay_with_jitter,
    _calculate_retry_delay_with_jitter,
    # Handler functions
    _handle_timeout_error,
    _handle_connection_error,
    _handle_payload_error,
    _handle_response_error,
    _handle_agent_error,
    _handle_json_error,
    _handle_unexpected_error,
    # Decorators
    handle_agent_errors,
    with_error_handling,
    handle_stream_errors,
    # Sanitization
    sanitize_error,
    _SENSITIVE_PATTERNS,
)
