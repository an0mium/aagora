"""
Shared imports and constants for API-based agents.

This module provides common imports used across all agent implementations
to avoid code duplication.
"""

import asyncio
import aiohttp
import json
import logging
import os
import random
import re
import threading
import time
from dataclasses import dataclass
from typing import Optional

from aragora.agents.base import CritiqueMixin
from aragora.agents.errors import (
    AgentCircuitOpenError,
    AgentConnectionError,
    AgentRateLimitError,
    AgentTimeoutError,
    handle_agent_errors,
)
from aragora.agents.registry import AgentRegistry
from aragora.config import DB_TIMEOUT_SECONDS, get_api_key
from aragora.core import Agent, Critique, Message
from aragora.server.error_utils import sanitize_error_text as _sanitize_error_message

logger = logging.getLogger(__name__)

# Maximum buffer size for streaming responses (prevents DoS via memory exhaustion)
MAX_STREAM_BUFFER_SIZE = 10 * 1024 * 1024  # 10MB


def calculate_retry_delay(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter_factor: float = 0.3,
) -> float:
    """
    Calculate retry delay with exponential backoff and random jitter.

    Jitter prevents thundering herd when multiple clients recover simultaneously
    after a provider outage. The delay is randomized within a range around the
    exponential backoff value.

    Args:
        attempt: Current retry attempt (0-indexed)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay cap in seconds (default: 60.0)
        jitter_factor: Fraction of delay to randomize (default: 0.3 = ±30%)

    Returns:
        Delay in seconds with jitter applied

    Example:
        attempt=0: ~1s (0.7-1.3s with 30% jitter)
        attempt=1: ~2s (1.4-2.6s)
        attempt=2: ~4s (2.8-5.2s)
        attempt=3: ~8s (5.6-10.4s)
    """
    # Calculate base exponential delay
    delay = min(base_delay * (2 ** attempt), max_delay)

    # Apply random jitter: delay ± (jitter_factor * delay)
    jitter = delay * jitter_factor * random.uniform(-1, 1)

    # Ensure minimum delay of 0.1s
    return max(0.1, delay + jitter)

__all__ = [
    # Standard library
    "asyncio",
    "aiohttp",
    "json",
    "logging",
    "os",
    "random",
    "re",
    "threading",
    "time",
    "dataclass",
    "Optional",
    # Aragora imports
    "CritiqueMixin",
    "AgentCircuitOpenError",
    "AgentConnectionError",
    "AgentRateLimitError",
    "AgentTimeoutError",
    "handle_agent_errors",
    "AgentRegistry",
    "DB_TIMEOUT_SECONDS",
    "get_api_key",
    "Agent",
    "Critique",
    "Message",
    "_sanitize_error_message",
    # Module-level
    "logger",
    "MAX_STREAM_BUFFER_SIZE",
    "calculate_retry_delay",
]
