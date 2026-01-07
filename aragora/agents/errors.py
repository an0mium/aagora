"""
Standardized error handling for agent operations.

Provides:
- Custom exception hierarchy for agent errors
- Centralized error classification for fallback decisions
- Async error handling decorators with retry logic
- Structured error logging with sanitization
"""

import asyncio
import functools
import logging
import random
import re
import subprocess
from typing import Any, Callable, Optional, Type, TypeVar

import aiohttp

logger = logging.getLogger(__name__)


# =============================================================================
# Error Pattern Constants
# =============================================================================

# Patterns that indicate rate limiting, quota errors, or service issues
RATE_LIMIT_PATTERNS: tuple[str, ...] = (
    # Rate limiting
    "rate limit", "rate_limit", "ratelimit",
    "429", "too many requests",
    "throttl",  # throttled, throttling
    # Quota/usage limit errors
    "quota exceeded", "quota_exceeded",
    "resource exhausted", "resource_exhausted",
    "insufficient_quota", "limit exceeded",
    "usage_limit", "usage limit",
    "limit has been reached",
    # Billing errors
    "billing", "credit balance", "payment required",
    "purchase credits", "402",
)

NETWORK_ERROR_PATTERNS: tuple[str, ...] = (
    # Capacity/availability errors
    "503", "service unavailable",
    "502", "bad gateway",
    "overloaded", "capacity",
    "temporarily unavailable", "try again later",
    "server busy", "high demand",
    # Connection errors
    "connection refused", "connection reset",
    "timed out", "timeout",
    "network error", "socket error",
    "could not resolve host", "name or service not known",
    "econnrefused", "econnreset", "etimedout",
    "no route to host", "network is unreachable",
)

CLI_ERROR_PATTERNS: tuple[str, ...] = (
    # API-specific errors
    "model overloaded", "model is currently overloaded",
    "engine is currently overloaded",
    "model_not_found", "model not found",
    "invalid_api_key", "invalid api key", "unauthorized",
    "authentication failed", "auth error",
    # CLI-specific errors
    "argument list too long",  # E2BIG - prompt too large for CLI
    "command not found", "no such file or directory",
    "permission denied", "access denied",
    "broken pipe",  # EPIPE - connection closed unexpectedly
)

# Combined patterns for fallback decisions (all error types that should trigger fallback)
ALL_FALLBACK_PATTERNS: tuple[str, ...] = (
    RATE_LIMIT_PATTERNS + NETWORK_ERROR_PATTERNS + CLI_ERROR_PATTERNS
)

# Type variable for generic return types
T = TypeVar("T")


# =============================================================================
# Custom Exception Hierarchy
# =============================================================================


class AgentError(Exception):
    """Base exception for all agent errors."""

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        cause: Exception | None = None,
        recoverable: bool = True,
    ) -> None:
        super().__init__(message)
        self.agent_name = agent_name
        self.cause = cause
        self.recoverable = recoverable

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.agent_name:
            parts.insert(0, f"[{self.agent_name}]")
        if self.cause:
            parts.append(f"(caused by: {type(self.cause).__name__}: {self.cause})")
        return " ".join(parts)


class AgentConnectionError(AgentError):
    """Network connection or HTTP errors."""

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        status_code: int | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, agent_name, cause, recoverable=True)
        self.status_code = status_code


class AgentTimeoutError(AgentError):
    """Timeout during agent operation."""

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        timeout_seconds: float | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, agent_name, cause, recoverable=True)
        self.timeout_seconds = timeout_seconds


class AgentRateLimitError(AgentError):
    """Rate limit or quota exceeded."""

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        retry_after: float | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, agent_name, cause, recoverable=True)
        self.retry_after = retry_after


class AgentAPIError(AgentError):
    """API-specific error (invalid request, auth failure, etc.)."""

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        status_code: int | None = None,
        error_type: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        # 4xx errors are generally not recoverable (bad request, auth)
        recoverable = status_code is None or status_code >= 500
        super().__init__(message, agent_name, cause, recoverable=recoverable)
        self.status_code = status_code
        self.error_type = error_type


class AgentResponseError(AgentError):
    """Error parsing or validating agent response."""

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        response_data: Any = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, agent_name, cause, recoverable=False)
        self.response_data = response_data


class AgentStreamError(AgentError):
    """Error during streaming response."""

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        partial_content: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, agent_name, cause, recoverable=True)
        self.partial_content = partial_content


class AgentCircuitOpenError(AgentError):
    """Circuit breaker is open, blocking requests to agent.

    This error is raised when too many consecutive failures have occurred
    and the circuit breaker has opened to protect the system from cascading
    failures. The request should be retried after the cooldown period.
    """

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        cooldown_seconds: float | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, agent_name, cause, recoverable=True)
        self.cooldown_seconds = cooldown_seconds


# =============================================================================
# CLI Agent Errors
# =============================================================================


class CLIAgentError(AgentError):
    """Base class for CLI agent errors."""

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        returncode: int | None = None,
        stderr: str | None = None,
        cause: Exception | None = None,
        recoverable: bool = True,
    ) -> None:
        super().__init__(message, agent_name, cause, recoverable)
        self.returncode = returncode
        self.stderr = stderr


class CLIParseError(CLIAgentError):
    """Error parsing CLI agent output (invalid JSON, etc.)."""

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        returncode: int | None = None,
        stderr: str | None = None,
        raw_output: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, agent_name, returncode, stderr, cause, recoverable=False)
        self.raw_output = raw_output


class CLITimeoutError(CLIAgentError):
    """CLI agent subprocess timed out."""

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        timeout_seconds: float | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, agent_name, returncode=-9, cause=cause, recoverable=True)
        self.timeout_seconds = timeout_seconds


class CLISubprocessError(CLIAgentError):
    """CLI subprocess failed with non-zero exit code."""

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        returncode: int | None = None,
        stderr: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        # Non-zero exit codes are generally recoverable (transient failures)
        super().__init__(message, agent_name, returncode, stderr, cause, recoverable=True)


class CLINotFoundError(CLIAgentError):
    """CLI tool not found or not installed."""

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        cli_name: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, agent_name, returncode=127, cause=cause, recoverable=False)
        self.cli_name = cli_name


# =============================================================================
# Error Context and Action Dataclasses
# =============================================================================


from dataclasses import dataclass


@dataclass
class ErrorContext:
    """Context for error handling decisions."""

    agent_name: str
    attempt: int
    max_retries: int
    retry_delay: float
    max_delay: float
    timeout: float | None = None


@dataclass
class ErrorAction:
    """Result of error classification for retry/handling decisions."""

    error: "AgentError"
    should_retry: bool
    delay_seconds: float = 0.0
    log_level: str = "warning"


# =============================================================================
# Error Classification Utilities
# =============================================================================


class ErrorClassifier:
    """Centralized error classification for fallback and retry decisions.

    Provides consistent error classification across CLI and API agents.
    Use this class to determine if an error should trigger fallback,
    retry, or other recovery mechanisms.

    Example:
        classifier = ErrorClassifier()

        # Check if exception should trigger fallback
        if classifier.should_fallback(error):
            return await fallback_agent.generate(prompt)

        # Check specific error types
        if classifier.is_rate_limit("Error: 429 Too Many Requests"):
            await asyncio.sleep(retry_after)
    """

    # OS error numbers that indicate connection/network issues
    NETWORK_ERRNO: frozenset[int] = frozenset({
        7,    # E2BIG - Argument list too long (prompt too large for CLI)
        32,   # EPIPE - Broken pipe (connection closed)
        104,  # ECONNRESET - Connection reset by peer
        110,  # ETIMEDOUT - Connection timed out
        111,  # ECONNREFUSED - Connection refused
        113,  # EHOSTUNREACH - No route to host
    })

    @classmethod
    def is_rate_limit(cls, error_message: str) -> bool:
        """Check if error message indicates rate limiting or quota exceeded.

        Args:
            error_message: Error message string to check

        Returns:
            True if error indicates rate limiting
        """
        error_lower = error_message.lower()
        return any(pattern in error_lower for pattern in RATE_LIMIT_PATTERNS)

    @classmethod
    def is_network_error(cls, error_message: str) -> bool:
        """Check if error message indicates network/connection issues.

        Args:
            error_message: Error message string to check

        Returns:
            True if error indicates network issues
        """
        error_lower = error_message.lower()
        return any(pattern in error_lower for pattern in NETWORK_ERROR_PATTERNS)

    @classmethod
    def is_cli_error(cls, error_message: str) -> bool:
        """Check if error message indicates CLI-specific issues.

        Args:
            error_message: Error message string to check

        Returns:
            True if error indicates CLI issues
        """
        error_lower = error_message.lower()
        return any(pattern in error_lower for pattern in CLI_ERROR_PATTERNS)

    @classmethod
    def should_fallback(cls, error: Exception) -> bool:
        """Determine if an exception should trigger fallback to alternative agent.

        Checks exception type and message for patterns that indicate the
        primary agent is unavailable and fallback should be attempted.

        Args:
            error: The exception to classify

        Returns:
            True if fallback should be attempted
        """
        error_str = str(error).lower()

        # Check for pattern matches in error message
        if any(pattern in error_str for pattern in ALL_FALLBACK_PATTERNS):
            return True

        # Timeout errors should trigger fallback
        if isinstance(error, (TimeoutError, asyncio.TimeoutError)):
            return True

        # Connection errors should trigger fallback
        if isinstance(error, (ConnectionError, ConnectionRefusedError,
                              ConnectionResetError, BrokenPipeError)):
            return True

        # OS-level errors (file not found for CLI, etc.)
        if isinstance(error, OSError) and error.errno in cls.NETWORK_ERRNO:
            return True

        # CLI command failures
        if isinstance(error, RuntimeError):
            if "cli command failed" in error_str or "cli" in error_str:
                return True
            if any(kw in error_str for kw in ["api error", "http error", "status"]):
                return True

        # Subprocess errors
        if isinstance(error, subprocess.SubprocessError):
            return True

        return False

    @classmethod
    def get_error_category(cls, error: Exception) -> str:
        """Get the category of an error for logging/metrics.

        Args:
            error: The exception to categorize

        Returns:
            Category string: "rate_limit", "network", "cli", "timeout", or "unknown"
        """
        error_str = str(error).lower()

        if isinstance(error, (TimeoutError, asyncio.TimeoutError)):
            return "timeout"

        if cls.is_rate_limit(error_str):
            return "rate_limit"

        if cls.is_network_error(error_str) or isinstance(
            error, (ConnectionError, ConnectionRefusedError,
                    ConnectionResetError, BrokenPipeError)
        ):
            return "network"

        if cls.is_cli_error(error_str) or isinstance(error, subprocess.SubprocessError):
            return "cli"

        return "unknown"


def classify_cli_error(
    returncode: int,
    stderr: str,
    stdout: str,
    agent_name: str | None = None,
    timeout_seconds: float | None = None,
) -> CLIAgentError:
    """
    Classify a CLI agent error based on return code and output.

    This function analyzes subprocess results to determine the appropriate
    error type for proper handling and retry decisions.

    Args:
        returncode: Subprocess exit code
        stderr: Standard error output
        stdout: Standard output
        agent_name: Name of the agent for error context
        timeout_seconds: Timeout value if applicable

    Returns:
        Appropriate CLIAgentError subclass instance
    """
    stderr_lower = stderr.lower() if stderr else ""
    stdout_lower = stdout.lower() if stdout else ""

    # Rate limit detection using centralized patterns
    if ErrorClassifier.is_rate_limit(stderr_lower):
        return CLIAgentError(
            f"Rate limit exceeded",
            agent_name=agent_name,
            returncode=returncode,
            stderr=stderr[:500] if stderr else None,
            recoverable=True,
        )

    # Timeout detection (SIGKILL = -9)
    if returncode == -9 or "timeout" in stderr_lower or "timed out" in stderr_lower:
        return CLITimeoutError(
            f"CLI command timed out after {timeout_seconds}s" if timeout_seconds else "CLI command timed out",
            agent_name=agent_name,
            timeout_seconds=timeout_seconds,
        )

    # Command not found
    if returncode == 127 or "command not found" in stderr_lower or "not found" in stderr_lower:
        return CLINotFoundError(
            f"CLI tool not found",
            agent_name=agent_name,
        )

    # Permission denied
    if returncode == 126 or "permission denied" in stderr_lower:
        return CLISubprocessError(
            f"Permission denied executing CLI",
            agent_name=agent_name,
            returncode=returncode,
            stderr=stderr[:500] if stderr else None,
        )

    # JSON parse error detection
    if stdout and not stdout.strip():
        return CLIParseError(
            f"Empty response from CLI",
            agent_name=agent_name,
            returncode=returncode,
            stderr=stderr[:500] if stderr else None,
            raw_output=stdout[:200] if stdout else None,
        )

    # Check for JSON error responses
    if stdout and stdout.strip().startswith("{"):
        try:
            import json
            data = json.loads(stdout)
            if "error" in data:
                return CLIAgentError(
                    f"CLI returned error: {data.get('error', 'Unknown error')[:200]}",
                    agent_name=agent_name,
                    returncode=returncode,
                    stderr=stderr[:500] if stderr else None,
                    recoverable=True,
                )
        except json.JSONDecodeError:
            return CLIParseError(
                f"Invalid JSON response from CLI",
                agent_name=agent_name,
                returncode=returncode,
                stderr=stderr[:500] if stderr else None,
                raw_output=stdout[:200] if stdout else None,
            )

    # Generic subprocess error
    return CLISubprocessError(
        f"CLI exited with code {returncode}: {stderr[:200] if stderr else 'no error output'}",
        agent_name=agent_name,
        returncode=returncode,
        stderr=stderr[:500] if stderr else None,
    )


# =============================================================================
# Sensitive Data Sanitization
# =============================================================================

# Import shared sanitization utilities
from aragora.utils.error_sanitizer import (
    sanitize_error,
    SENSITIVE_PATTERNS as _SENSITIVE_PATTERNS,  # For backwards compatibility
)


# =============================================================================
# Retry Delay Calculation
# =============================================================================


def _calculate_retry_delay_with_jitter(
    attempt: int,
    base_delay: float,
    max_delay: float,
    jitter_factor: float = 0.3,
) -> float:
    """
    Calculate retry delay with exponential backoff and random jitter.

    Jitter prevents thundering herd when multiple clients recover simultaneously
    after a provider outage.

    Args:
        attempt: Current retry attempt (0-indexed)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        jitter_factor: Fraction of delay to randomize (default: 0.3 = ±30%)

    Returns:
        Delay in seconds with jitter applied
    """
    # Calculate base exponential delay
    delay = min(base_delay * (2 ** attempt), max_delay)

    # Apply random jitter: delay ± (jitter_factor * delay)
    jitter = delay * jitter_factor * random.uniform(-1, 1)

    # Ensure minimum delay of 0.1s
    return max(0.1, delay + jitter)


# =============================================================================
# Error Handler Functions
# =============================================================================


def _handle_timeout_error(
    e: asyncio.TimeoutError,
    ctx: ErrorContext,
    retryable_exceptions: tuple,
) -> ErrorAction:
    """Handle timeout errors."""
    error = AgentTimeoutError(
        f"Operation timed out after {ctx.timeout}s",
        agent_name=ctx.agent_name,
        timeout_seconds=ctx.timeout,
        cause=e,
    )
    should_retry = (
        ctx.max_retries > 0
        and ctx.attempt <= ctx.max_retries
        and isinstance(error, retryable_exceptions)
    )
    delay = _calculate_retry_delay_with_jitter(
        ctx.attempt - 1, ctx.retry_delay, ctx.max_delay
    ) if should_retry else 0.0

    return ErrorAction(error=error, should_retry=should_retry, delay_seconds=delay)


def _handle_connection_error(
    e: aiohttp.ClientConnectorError | aiohttp.ServerDisconnectedError,
    ctx: ErrorContext,
    retryable_exceptions: tuple,
) -> ErrorAction:
    """Handle connection/network errors."""
    if isinstance(e, aiohttp.ServerDisconnectedError):
        msg = f"Server disconnected: {sanitize_error(str(e))}"
    else:
        msg = f"Connection failed: {sanitize_error(str(e))}"

    error = AgentConnectionError(
        msg,
        agent_name=ctx.agent_name,
        cause=e,
    )
    should_retry = (
        ctx.max_retries > 0
        and ctx.attempt <= ctx.max_retries
        and isinstance(error, retryable_exceptions)
    )
    delay = _calculate_retry_delay_with_jitter(
        ctx.attempt - 1, ctx.retry_delay, ctx.max_delay
    ) if should_retry else 0.0

    return ErrorAction(error=error, should_retry=should_retry, delay_seconds=delay)


def _handle_payload_error(
    e: aiohttp.ClientPayloadError,
    ctx: ErrorContext,
    retryable_exceptions: tuple,
) -> ErrorAction:
    """Handle streaming payload errors."""
    error = AgentStreamError(
        f"Payload error during streaming: {sanitize_error(str(e))}",
        agent_name=ctx.agent_name,
        cause=e,
    )
    should_retry = (
        ctx.max_retries > 0
        and ctx.attempt <= ctx.max_retries
        and isinstance(error, retryable_exceptions)
    )
    delay = _calculate_retry_delay_with_jitter(
        ctx.attempt - 1, ctx.retry_delay, ctx.max_delay
    ) if should_retry else 0.0

    return ErrorAction(error=error, should_retry=should_retry, delay_seconds=delay)


def _handle_response_error(
    e: aiohttp.ClientResponseError,
    ctx: ErrorContext,
    retryable_exceptions: tuple,
) -> ErrorAction:
    """Handle HTTP response errors (429, 5xx, 4xx)."""
    if e.status == 429:
        # Rate limit - check for Retry-After header
        retry_after = None
        if e.headers and "Retry-After" in e.headers:
            try:
                retry_after = float(e.headers["Retry-After"])
            except (ValueError, TypeError):
                pass

        error = AgentRateLimitError(
            "Rate limit exceeded (HTTP 429)",
            agent_name=ctx.agent_name,
            retry_after=retry_after,
            cause=e,
        )
        should_retry = (
            ctx.max_retries > 0
            and ctx.attempt <= ctx.max_retries
            and isinstance(error, retryable_exceptions)
        )

        # Use Retry-After if available, otherwise use backoff
        if should_retry and retry_after:
            base_wait = min(retry_after, ctx.max_delay)
            jitter = base_wait * 0.1 * random.uniform(0, 1)
            delay = base_wait + jitter
        elif should_retry:
            delay = _calculate_retry_delay_with_jitter(
                ctx.attempt - 1, ctx.retry_delay, ctx.max_delay
            )
        else:
            delay = 0.0

        return ErrorAction(error=error, should_retry=should_retry, delay_seconds=delay)

    elif e.status >= 500:
        error = AgentConnectionError(
            f"Server error (HTTP {e.status})",
            agent_name=ctx.agent_name,
            status_code=e.status,
            cause=e,
        )
        should_retry = (
            ctx.max_retries > 0
            and ctx.attempt <= ctx.max_retries
            and isinstance(error, retryable_exceptions)
        )
        delay = _calculate_retry_delay_with_jitter(
            ctx.attempt - 1, ctx.retry_delay, ctx.max_delay
        ) if should_retry else 0.0

        return ErrorAction(error=error, should_retry=should_retry, delay_seconds=delay)

    else:
        # 4xx errors - not retryable
        error = AgentAPIError(
            f"API error (HTTP {e.status}): {sanitize_error(str(e))}",
            agent_name=ctx.agent_name,
            status_code=e.status,
            cause=e,
        )
        return ErrorAction(
            error=error, should_retry=False, delay_seconds=0.0, log_level="error"
        )


def _handle_agent_error(
    e: AgentError,
    ctx: ErrorContext,
    retryable_exceptions: tuple,
) -> ErrorAction:
    """Handle already-wrapped AgentError exceptions."""
    e.agent_name = e.agent_name or ctx.agent_name

    if not e.recoverable:
        return ErrorAction(
            error=e, should_retry=False, delay_seconds=0.0, log_level="error"
        )

    should_retry = (
        ctx.max_retries > 0
        and ctx.attempt <= ctx.max_retries
        and isinstance(e, retryable_exceptions)
    )
    delay = _calculate_retry_delay_with_jitter(
        ctx.attempt - 1, ctx.retry_delay, ctx.max_delay
    ) if should_retry else 0.0

    return ErrorAction(error=e, should_retry=should_retry, delay_seconds=delay)


def _handle_json_error(e: ValueError, ctx: ErrorContext) -> ErrorAction:
    """Handle JSON decode errors."""
    error = AgentResponseError(
        f"Invalid JSON response: {sanitize_error(str(e))}",
        agent_name=ctx.agent_name,
        cause=e,
    )
    return ErrorAction(
        error=error, should_retry=False, delay_seconds=0.0, log_level="error"
    )


def _handle_unexpected_error(e: Exception, ctx: ErrorContext) -> ErrorAction:
    """Handle unexpected/unknown errors."""
    error = AgentError(
        f"Unexpected error: {sanitize_error(str(e))}",
        agent_name=ctx.agent_name,
        cause=e,
        recoverable=False,
    )
    return ErrorAction(
        error=error, should_retry=False, delay_seconds=0.0, log_level="error"
    )


# =============================================================================
# Error Handling Decorators
# =============================================================================


def handle_agent_errors(
    agent_name_attr: str = "name",
    max_retries: int = 0,
    retry_delay: float = 1.0,
    retry_backoff: float = 2.0,
    max_delay: float = 30.0,
    retryable_exceptions: tuple = (AgentConnectionError, AgentTimeoutError, AgentRateLimitError),
    circuit_breaker_attr: str = "_circuit_breaker",
):
    """
    Decorator for async agent methods that standardizes error handling.

    Wraps aiohttp and other common exceptions in AgentError types,
    logs errors appropriately, and optionally retries transient failures.
    Integrates with CircuitBreaker for graceful failure handling.

    Args:
        agent_name_attr: Attribute name on self containing agent name
        max_retries: Maximum retry attempts for recoverable errors (0 = no retry)
        retry_delay: Initial delay between retries in seconds
        retry_backoff: Multiplier for delay between retries
        max_delay: Maximum delay between retries
        retryable_exceptions: Tuple of AgentError subclasses to retry
        circuit_breaker_attr: Attribute name on self for CircuitBreaker instance.
            If the attribute exists and circuit is open, raises AgentCircuitOpenError.
            Records success/failure to circuit breaker after each attempt.

    Usage:
        @handle_agent_errors(max_retries=3)
        async def generate(self, prompt: str) -> str:
            async with aiohttp.ClientSession() as session:
                ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs) -> T:
            agent_name = getattr(self, agent_name_attr, "unknown")
            circuit_breaker = getattr(self, circuit_breaker_attr, None)

            # Check circuit breaker before attempting call
            if circuit_breaker is not None and not circuit_breaker.can_proceed():
                raise AgentCircuitOpenError(
                    "Circuit breaker is open for agent",
                    agent_name=agent_name,
                    cooldown_seconds=circuit_breaker.cooldown_seconds,
                )

            attempt = 0
            ctx = ErrorContext(
                agent_name=agent_name,
                attempt=0,
                max_retries=max_retries,
                retry_delay=retry_delay,
                max_delay=max_delay,
                timeout=getattr(self, "timeout", None),
            )

            while True:
                attempt += 1
                ctx.attempt = attempt

                try:
                    result = await func(self, *args, **kwargs)
                    if circuit_breaker is not None:
                        circuit_breaker.record_success()
                    return result

                except asyncio.TimeoutError as e:
                    action = _handle_timeout_error(e, ctx, retryable_exceptions)

                except (aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError) as e:
                    action = _handle_connection_error(e, ctx, retryable_exceptions)

                except aiohttp.ClientPayloadError as e:
                    action = _handle_payload_error(e, ctx, retryable_exceptions)

                except aiohttp.ClientResponseError as e:
                    action = _handle_response_error(e, ctx, retryable_exceptions)

                except AgentError as e:
                    action = _handle_agent_error(e, ctx, retryable_exceptions)
                    if not e.recoverable:
                        raise

                except ValueError as e:
                    if "json" in str(e).lower() or "decode" in str(e).lower():
                        action = _handle_json_error(e, ctx)
                        logger.error(f"[{agent_name}] Response parse error: {action.error}")
                        raise action.error from e
                    raise

                except Exception as e:
                    action = _handle_unexpected_error(e, ctx)
                    logger.error(
                        f"[{agent_name}] Unexpected error (attempt {attempt}): {action.error}",
                        exc_info=True,
                    )
                    if circuit_breaker is not None:
                        circuit_breaker.record_failure()
                    raise action.error from e

                # Log the error at appropriate level
                log_method = getattr(logger, action.log_level, logger.warning)
                log_method(f"[{agent_name}] {type(action.error).__name__} (attempt {attempt}): {action.error}")

                # Record failure to circuit breaker
                if circuit_breaker is not None:
                    circuit_breaker.record_failure()

                # Retry if appropriate
                if action.should_retry and action.error.recoverable:
                    logger.info(
                        f"[{agent_name}] Retrying in {action.delay_seconds:.1f}s "
                        f"(attempt {attempt}/{max_retries + 1})"
                    )
                    await asyncio.sleep(action.delay_seconds)
                    continue

                # No more retries - raise the error
                raise action.error

        return wrapper

    return decorator


def with_error_handling(
    error_types: tuple[Type[Exception], ...] = (Exception,),
    fallback: Any = None,
    log_level: str = "warning",
    reraise: bool = False,
    message_template: str | None = None,
):
    """
    Simple decorator for standardized exception handling with logging.

    Use this for non-agent functions where you want consistent error
    handling without the full retry/circuit-breaker infrastructure.
    Reduces boilerplate try/except/log patterns throughout the codebase.

    Args:
        error_types: Tuple of exception types to catch (default: all Exception)
        fallback: Value to return when exception is caught (default: None)
        log_level: Logging level for caught errors ("debug", "info", "warning", "error")
        reraise: If True, re-raise after logging (default: False)
        message_template: Custom log message template. Use {func}, {error}, {error_type}

    Usage:
        # Basic usage - log warning and return None on any error
        @with_error_handling()
        def risky_function():
            ...

        # Catch specific errors, return fallback value
        @with_error_handling(error_types=(ValueError, KeyError), fallback=[])
        def parse_data(data):
            ...

        # Log at debug level for expected errors
        @with_error_handling(error_types=(FileNotFoundError,), log_level="debug")
        def load_optional_config():
            ...

        # Log and re-raise for critical paths
        @with_error_handling(reraise=True, log_level="error")
        async def important_operation():
            ...

    Example conversion:
        # Before (boilerplate):
        def my_func():
            try:
                return do_something()
            except ValueError as e:
                logger.warning(f"my_func error: {e}")
                return None

        # After (using decorator):
        @with_error_handling(error_types=(ValueError,))
        def my_func():
            return do_something()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except error_types as e:
                _log_error(func, e, log_level, message_template)
                if reraise:
                    raise
                return fallback

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except error_types as e:
                _log_error(func, e, log_level, message_template)
                if reraise:
                    raise
                return fallback

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _log_error(
    func: Callable,
    error: Exception,
    log_level: str,
    message_template: str | None,
) -> None:
    """Helper to log errors with consistent formatting."""
    if message_template:
        message = message_template.format(
            func=func.__name__,
            error=error,
            error_type=type(error).__name__,
        )
    else:
        message = f"{func.__name__} error: {type(error).__name__}: {error}"

    # Get the appropriate log method
    log_method = getattr(logger, log_level, logger.warning)
    log_method(message)


def handle_stream_errors(agent_name_attr: str = "name"):
    """
    Decorator specifically for streaming methods.

    Wraps errors that occur during async iteration and attempts to
    preserve any partial content received.

    Usage:
        @handle_stream_errors()
        async def generate_stream(self, prompt: str):
            async for chunk in ...:
                yield chunk
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            agent_name = getattr(self, agent_name_attr, "unknown")
            partial_content = []

            try:
                async for chunk in func(self, *args, **kwargs):
                    if isinstance(chunk, str):
                        partial_content.append(chunk)
                    yield chunk

            except asyncio.TimeoutError as e:
                timeout = getattr(self, "timeout", None)
                raise AgentTimeoutError(
                    f"Stream timed out after {timeout}s",
                    agent_name=agent_name,
                    timeout_seconds=timeout,
                    partial_content="".join(partial_content) if partial_content else None,
                    cause=e,
                ) from e

            except (aiohttp.ClientPayloadError, aiohttp.ServerDisconnectedError) as e:
                raise AgentStreamError(
                    f"Stream interrupted: {sanitize_error(str(e))}",
                    agent_name=agent_name,
                    partial_content="".join(partial_content) if partial_content else None,
                    cause=e,
                ) from e

            except AgentError:
                raise

            except Exception as e:
                raise AgentStreamError(
                    f"Unexpected stream error: {sanitize_error(str(e))}",
                    agent_name=agent_name,
                    partial_content="".join(partial_content) if partial_content else None,
                    cause=e,
                ) from e

        return wrapper

    return decorator
