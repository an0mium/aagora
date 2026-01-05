"""
Aragora Configuration.

Centralized configuration with environment variable overrides.
Import these values instead of hardcoding throughout the codebase.
"""

import os
from typing import Optional


def _env_int(key: str, default: int) -> int:
    """Get integer from environment with fallback."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def _env_float(key: str, default: float) -> float:
    """Get float from environment with fallback."""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


def _env_str(key: str, default: str) -> str:
    """Get string from environment with fallback."""
    return os.getenv(key, default)


def _env_bool(key: str, default: bool) -> bool:
    """Get boolean from environment with fallback."""
    val = os.getenv(key, str(default)).lower()
    return val in ("true", "1", "yes", "on")


# === Authentication ===
TOKEN_TTL_SECONDS = _env_int("ARAGORA_TOKEN_TTL", 3600)
SHAREABLE_LINK_TTL = _env_int("ARAGORA_SHAREABLE_LINK_TTL", 3600)

# === Rate Limiting ===
DEFAULT_RATE_LIMIT = _env_int("ARAGORA_RATE_LIMIT", 60)  # requests per minute
IP_RATE_LIMIT = _env_int("ARAGORA_IP_RATE_LIMIT", 120)

# === API Limits ===
MAX_API_LIMIT = _env_int("ARAGORA_MAX_API_LIMIT", 100)
DEFAULT_PAGINATION = _env_int("ARAGORA_DEFAULT_PAGINATION", 20)
MAX_CONTENT_LENGTH = _env_int("ARAGORA_MAX_CONTENT_LENGTH", 100 * 1024 * 1024)  # 100MB
MAX_QUESTION_LENGTH = _env_int("ARAGORA_MAX_QUESTION_LENGTH", 10000)

# === Debate Defaults ===
DEFAULT_ROUNDS = _env_int("ARAGORA_DEFAULT_ROUNDS", 3)
MAX_ROUNDS = _env_int("ARAGORA_MAX_ROUNDS", 10)
DEFAULT_CONSENSUS = _env_str("ARAGORA_DEFAULT_CONSENSUS", "hybrid")
DEBATE_TIMEOUT_SECONDS = _env_int("ARAGORA_DEBATE_TIMEOUT", 600)  # 10 minutes

# === Agents ===
DEFAULT_AGENTS = _env_str(
    "ARAGORA_DEFAULT_AGENTS",
    "grok,anthropic-api,openai-api,deepseek,gemini"
)
STREAMING_CAPABLE_AGENTS = _env_str(
    "ARAGORA_STREAMING_AGENTS",
    "grok,anthropic-api,openai-api"
)

# === Caching TTLs (seconds) ===
CACHE_TTL_LEADERBOARD = _env_int("ARAGORA_CACHE_LEADERBOARD", 300)  # 5 min
CACHE_TTL_AGENT_PROFILE = _env_int("ARAGORA_CACHE_AGENT_PROFILE", 600)  # 10 min
CACHE_TTL_RECENT_MATCHES = _env_int("ARAGORA_CACHE_RECENT_MATCHES", 120)  # 2 min
CACHE_TTL_ANALYTICS = _env_int("ARAGORA_CACHE_ANALYTICS", 600)  # 10 min
CACHE_TTL_CONSENSUS = _env_int("ARAGORA_CACHE_CONSENSUS", 240)  # 4 min

# === WebSocket ===
WS_MAX_MESSAGE_SIZE = _env_int("ARAGORA_WS_MAX_MESSAGE_SIZE", 16 * 1024 * 1024)  # 16MB
WS_HEARTBEAT_INTERVAL = _env_int("ARAGORA_WS_HEARTBEAT", 30)

# === Storage ===
DEFAULT_STORAGE_DIR = _env_str("ARAGORA_STORAGE_DIR", ".aragora")
MAX_LOG_BYTES = _env_int("ARAGORA_MAX_LOG_BYTES", 100 * 1024)  # 100KB

# === Evidence Collection ===
MAX_SNIPPETS_PER_CONNECTOR = _env_int("ARAGORA_MAX_SNIPPETS_CONNECTOR", 3)
MAX_TOTAL_SNIPPETS = _env_int("ARAGORA_MAX_TOTAL_SNIPPETS", 8)
SNIPPET_MAX_LENGTH = _env_int("ARAGORA_SNIPPET_MAX_LENGTH", 1000)

# === Deep Audit ===
DEEP_AUDIT_ROUNDS = _env_int("ARAGORA_DEEP_AUDIT_ROUNDS", 6)
CROSS_EXAMINATION_DEPTH = _env_int("ARAGORA_CROSS_EXAM_DEPTH", 3)
RISK_THRESHOLD = _env_float("ARAGORA_RISK_THRESHOLD", 0.7)

# === ELO System ===
ELO_INITIAL_RATING = _env_int("ARAGORA_ELO_INITIAL", 1500)
ELO_K_FACTOR = _env_int("ARAGORA_ELO_K_FACTOR", 32)
