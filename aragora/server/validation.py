"""
Request validation middleware for Aragora server.

Provides JSON schema validation for POST endpoints, content-type
verification, and request body size limits.
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Max JSON body size (1MB by default, lower than file upload limit)
MAX_JSON_BODY_SIZE = 1 * 1024 * 1024

# Safe string patterns
SAFE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')
SAFE_ID_PATTERN_WITH_DOTS = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$')
SAFE_SLUG_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,128}$')
SAFE_AGENT_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,32}$')


@dataclass
class ValidationResult:
    """Result of validation check."""
    is_valid: bool
    error: Optional[str] = None
    data: Optional[Any] = None


def validate_json_body(
    body: bytes,
    max_size: int = MAX_JSON_BODY_SIZE,
) -> ValidationResult:
    """Validate JSON body for size and format.

    Args:
        body: Raw request body bytes
        max_size: Maximum allowed size in bytes

    Returns:
        ValidationResult with parsed data or error
    """
    if len(body) > max_size:
        return ValidationResult(
            is_valid=False,
            error=f"Request body too large. Max size: {max_size // 1024}KB"
        )

    if len(body) == 0:
        return ValidationResult(
            is_valid=False,
            error="Request body is empty"
        )

    try:
        data = json.loads(body.decode('utf-8'))
        return ValidationResult(is_valid=True, data=data)
    except json.JSONDecodeError as e:
        return ValidationResult(
            is_valid=False,
            error=f"Invalid JSON: {str(e)}"
        )
    except UnicodeDecodeError:
        return ValidationResult(
            is_valid=False,
            error="Invalid UTF-8 encoding in request body"
        )


def validate_content_type(content_type: str, expected: str = "application/json") -> ValidationResult:
    """Validate Content-Type header.

    Args:
        content_type: The Content-Type header value
        expected: Expected content type prefix

    Returns:
        ValidationResult with success or error
    """
    if not content_type:
        return ValidationResult(
            is_valid=False,
            error=f"Missing Content-Type header. Expected: {expected}"
        )

    if not content_type.lower().startswith(expected.lower()):
        return ValidationResult(
            is_valid=False,
            error=f"Invalid Content-Type: {content_type}. Expected: {expected}"
        )

    return ValidationResult(is_valid=True)


def validate_required_fields(data: dict, fields: list[str]) -> ValidationResult:
    """Validate that required fields are present.

    Args:
        data: Parsed JSON data
        fields: List of required field names

    Returns:
        ValidationResult with success or error
    """
    missing = [f for f in fields if f not in data or data[f] is None]

    if missing:
        return ValidationResult(
            is_valid=False,
            error=f"Missing required fields: {', '.join(missing)}"
        )

    return ValidationResult(is_valid=True)


def validate_string_field(
    data: dict,
    field: str,
    min_length: int = 0,
    max_length: int = 1000,
    pattern: Optional[re.Pattern] = None,
    required: bool = True,
) -> ValidationResult:
    """Validate a string field.

    Args:
        data: Parsed JSON data
        field: Field name to validate
        min_length: Minimum string length
        max_length: Maximum string length
        pattern: Optional regex pattern to match
        required: Whether the field is required

    Returns:
        ValidationResult with success or error
    """
    value = data.get(field)

    if value is None:
        if required:
            return ValidationResult(
                is_valid=False,
                error=f"Missing required field: {field}"
            )
        return ValidationResult(is_valid=True)

    if not isinstance(value, str):
        return ValidationResult(
            is_valid=False,
            error=f"Field '{field}' must be a string"
        )

    if len(value) < min_length:
        return ValidationResult(
            is_valid=False,
            error=f"Field '{field}' must be at least {min_length} characters"
        )

    if len(value) > max_length:
        return ValidationResult(
            is_valid=False,
            error=f"Field '{field}' must be at most {max_length} characters"
        )

    if pattern and not pattern.match(value):
        return ValidationResult(
            is_valid=False,
            error=f"Field '{field}' has invalid format"
        )

    return ValidationResult(is_valid=True)


def validate_int_field(
    data: dict,
    field: str,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    required: bool = True,
) -> ValidationResult:
    """Validate an integer field.

    Args:
        data: Parsed JSON data
        field: Field name to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        required: Whether the field is required

    Returns:
        ValidationResult with success or error
    """
    value = data.get(field)

    if value is None:
        if required:
            return ValidationResult(
                is_valid=False,
                error=f"Missing required field: {field}"
            )
        return ValidationResult(is_valid=True)

    if not isinstance(value, int) or isinstance(value, bool):
        return ValidationResult(
            is_valid=False,
            error=f"Field '{field}' must be an integer"
        )

    if min_value is not None and value < min_value:
        return ValidationResult(
            is_valid=False,
            error=f"Field '{field}' must be at least {min_value}"
        )

    if max_value is not None and value > max_value:
        return ValidationResult(
            is_valid=False,
            error=f"Field '{field}' must be at most {max_value}"
        )

    return ValidationResult(is_valid=True)


def validate_float_field(
    data: dict,
    field: str,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    required: bool = True,
) -> ValidationResult:
    """Validate a float field.

    Args:
        data: Parsed JSON data
        field: Field name to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        required: Whether the field is required

    Returns:
        ValidationResult with success or error
    """
    value = data.get(field)

    if value is None:
        if required:
            return ValidationResult(
                is_valid=False,
                error=f"Missing required field: {field}"
            )
        return ValidationResult(is_valid=True)

    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return ValidationResult(
            is_valid=False,
            error=f"Field '{field}' must be a number"
        )

    if min_value is not None and value < min_value:
        return ValidationResult(
            is_valid=False,
            error=f"Field '{field}' must be at least {min_value}"
        )

    if max_value is not None and value > max_value:
        return ValidationResult(
            is_valid=False,
            error=f"Field '{field}' must be at most {max_value}"
        )

    return ValidationResult(is_valid=True)


def validate_list_field(
    data: dict,
    field: str,
    min_length: int = 0,
    max_length: int = 100,
    item_type: Optional[type] = None,
    required: bool = True,
) -> ValidationResult:
    """Validate a list field.

    Args:
        data: Parsed JSON data
        field: Field name to validate
        min_length: Minimum list length
        max_length: Maximum list length
        item_type: Expected type of list items
        required: Whether the field is required

    Returns:
        ValidationResult with success or error
    """
    value = data.get(field)

    if value is None:
        if required:
            return ValidationResult(
                is_valid=False,
                error=f"Missing required field: {field}"
            )
        return ValidationResult(is_valid=True)

    if not isinstance(value, list):
        return ValidationResult(
            is_valid=False,
            error=f"Field '{field}' must be a list"
        )

    if len(value) < min_length:
        return ValidationResult(
            is_valid=False,
            error=f"Field '{field}' must have at least {min_length} items"
        )

    if len(value) > max_length:
        return ValidationResult(
            is_valid=False,
            error=f"Field '{field}' must have at most {max_length} items"
        )

    if item_type is not None:
        for i, item in enumerate(value):
            if not isinstance(item, item_type):
                return ValidationResult(
                    is_valid=False,
                    error=f"Field '{field}[{i}]' must be of type {item_type.__name__}"
                )

    return ValidationResult(is_valid=True)


def validate_enum_field(
    data: dict,
    field: str,
    allowed_values: set,
    required: bool = True,
) -> ValidationResult:
    """Validate a field against allowed values.

    Args:
        data: Parsed JSON data
        field: Field name to validate
        allowed_values: Set of allowed values
        required: Whether the field is required

    Returns:
        ValidationResult with success or error
    """
    value = data.get(field)

    if value is None:
        if required:
            return ValidationResult(
                is_valid=False,
                error=f"Missing required field: {field}"
            )
        return ValidationResult(is_valid=True)

    if value not in allowed_values:
        allowed_str = ", ".join(str(v) for v in sorted(allowed_values))
        return ValidationResult(
            is_valid=False,
            error=f"Field '{field}' must be one of: {allowed_str}"
        )

    return ValidationResult(is_valid=True)


# Endpoint-specific validation schemas
DEBATE_START_SCHEMA = {
    "task": {"type": "string", "min_length": 1, "max_length": 2000, "required": True},
    "agents": {"type": "list", "min_length": 2, "max_length": 10, "item_type": str, "required": False},
    "mode": {"type": "string", "max_length": 64, "required": False},
    "rounds": {"type": "int", "min_value": 1, "max_value": 20, "required": False},
}

VERIFICATION_SCHEMA = {
    "claim": {"type": "string", "min_length": 1, "max_length": 5000, "required": True},
    "context": {"type": "string", "max_length": 10000, "required": False},
}

PROBE_RUN_SCHEMA = {
    "agent": {"type": "string", "min_length": 1, "max_length": 64, "pattern": SAFE_AGENT_PATTERN, "required": True},
    "strategies": {"type": "list", "max_length": 10, "item_type": str, "required": False},
    "num_probes": {"type": "int", "min_value": 1, "max_value": 50, "required": False},
}

FORK_REQUEST_SCHEMA = {
    "branch_point": {"type": "int", "min_value": 0, "max_value": 100, "required": True},
    "modified_context": {"type": "string", "max_length": 5000, "required": False},
}

MEMORY_CLEANUP_SCHEMA = {
    "tier": {"type": "enum", "allowed_values": {"fast", "medium", "slow", "glacial"}, "required": False},
    "archive": {"type": "string", "max_length": 10, "required": False},  # "true" or "false"
    "max_age_hours": {"type": "float", "min_value": 0.0, "max_value": 8760.0, "required": False},  # Max 1 year
}


def validate_against_schema(data: dict, schema: dict) -> ValidationResult:
    """Validate data against a schema definition.

    Args:
        data: Parsed JSON data
        schema: Schema definition dict

    Returns:
        ValidationResult with success or error
    """
    for field, rules in schema.items():
        field_type = rules.get("type", "string")
        required = rules.get("required", True)

        if field_type == "string":
            result = validate_string_field(
                data, field,
                min_length=rules.get("min_length", 0),
                max_length=rules.get("max_length", 1000),
                pattern=rules.get("pattern"),
                required=required,
            )
        elif field_type == "int":
            result = validate_int_field(
                data, field,
                min_value=rules.get("min_value"),
                max_value=rules.get("max_value"),
                required=required,
            )
        elif field_type == "float":
            result = validate_float_field(
                data, field,
                min_value=rules.get("min_value"),
                max_value=rules.get("max_value"),
                required=required,
            )
        elif field_type == "list":
            result = validate_list_field(
                data, field,
                min_length=rules.get("min_length", 0),
                max_length=rules.get("max_length", 100),
                item_type=rules.get("item_type"),
                required=required,
            )
        elif field_type == "enum":
            result = validate_enum_field(
                data, field,
                allowed_values=rules.get("allowed_values", set()),
                required=required,
            )
        else:
            continue  # Unknown type, skip

        if not result.is_valid:
            return result

    return ValidationResult(is_valid=True, data=data)


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize a string by stripping and truncating.

    Args:
        value: String to sanitize
        max_length: Maximum length to truncate to

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_length]


def sanitize_id(value: str) -> Optional[str]:
    """Sanitize an ID string.

    Args:
        value: ID string to sanitize

    Returns:
        Sanitized ID or None if invalid
    """
    if not isinstance(value, str):
        return None
    value = value.strip()
    if SAFE_ID_PATTERN.match(value):
        return value
    return None


# =============================================================================
# Path Segment Validation Functions
# =============================================================================
# These functions provide consistent security validation for path segments,
# preventing path traversal attacks and injection vulnerabilities.

def validate_path_segment(
    value: str,
    name: str,
    pattern: re.Pattern = None,
) -> Tuple[bool, Optional[str]]:
    """Validate a path segment against a pattern.

    This is the primary function for validating user-provided path segments
    like IDs, names, and slugs. It ensures values conform to safe patterns
    and prevents path traversal or injection attacks.

    Args:
        value: The value to validate
        name: Name of the segment for error messages
        pattern: Regex pattern to match against (defaults to SAFE_ID_PATTERN)

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> is_valid, err = validate_path_segment("my-debate-123", "debate_id")
        >>> if not is_valid:
        ...     return error_response(400, err)
    """
    if pattern is None:
        pattern = SAFE_ID_PATTERN

    if not value:
        return False, f"Missing {name}"
    if not pattern.match(value):
        return False, f"Invalid {name}: must match pattern {pattern.pattern}"
    return True, None


def validate_id(value: str, name: str = "ID") -> Tuple[bool, Optional[str]]:
    """Validate a generic ID (alphanumeric with hyphens/underscores, 1-64 chars).

    Args:
        value: ID to validate
        name: Name for error messages

    Returns:
        Tuple of (is_valid, error_message)
    """
    return validate_path_segment(value, name, SAFE_ID_PATTERN)


def validate_agent_name(agent: str) -> Tuple[bool, Optional[str]]:
    """Validate an agent name (alphanumeric with hyphens/underscores, 1-32 chars).

    Args:
        agent: Agent name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    return validate_path_segment(agent, "agent name", SAFE_AGENT_PATTERN)


def validate_debate_id(debate_id: str) -> Tuple[bool, Optional[str]]:
    """Validate a debate ID (alphanumeric with hyphens/underscores, 1-128 chars).

    Args:
        debate_id: Debate ID to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    return validate_path_segment(debate_id, "debate ID", SAFE_SLUG_PATTERN)


def validate_plugin_name(plugin_name: str) -> Tuple[bool, Optional[str]]:
    """Validate a plugin name.

    Args:
        plugin_name: Plugin name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    return validate_path_segment(plugin_name, "plugin name", SAFE_ID_PATTERN)


def validate_loop_id(loop_id: str) -> Tuple[bool, Optional[str]]:
    """Validate a nomic loop ID.

    Args:
        loop_id: Loop ID to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    return validate_path_segment(loop_id, "loop ID", SAFE_ID_PATTERN)


def validate_replay_id(replay_id: str) -> Tuple[bool, Optional[str]]:
    """Validate a replay ID.

    Args:
        replay_id: Replay ID to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    return validate_path_segment(replay_id, "replay ID", SAFE_ID_PATTERN)


def validate_genome_id(genome_id: str) -> Tuple[bool, Optional[str]]:
    """Validate a genome ID (supports dots for versioning).

    Args:
        genome_id: Genome ID to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    return validate_path_segment(genome_id, "genome ID", SAFE_ID_PATTERN_WITH_DOTS)


def validate_agent_name_with_version(agent: str) -> Tuple[bool, Optional[str]]:
    """Validate an agent name that may include version dots (e.g., claude-3.5-sonnet).

    Args:
        agent: Agent name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    return validate_path_segment(agent, "agent name", SAFE_ID_PATTERN_WITH_DOTS)


# =============================================================================
# Query Parameter Parsing Functions
# =============================================================================
# These functions provide safe parsing of URL query parameters with bounds
# checking and proper error handling. They work with the parse_qs format
# (dict with list values) used by urllib.parse.

def parse_int_param(
    query: Dict[str, list],
    key: str,
    default: int,
    min_val: int = 1,
    max_val: int = 100,
) -> int:
    """Safely parse an integer query parameter with bounds checking.

    Args:
        query: Query dict from parse_qs (values are lists)
        key: Parameter name
        default: Default value if missing or invalid
        min_val: Minimum allowed value (default 1)
        max_val: Maximum allowed value (default 100)

    Returns:
        Parsed integer clamped to [min_val, max_val], or default on error

    Example:
        >>> query = parse_qs("limit=50&offset=10")
        >>> limit = parse_int_param(query, "limit", default=20, max_val=100)
        >>> offset = parse_int_param(query, "offset", default=0, min_val=0)
    """
    try:
        values = query.get(key, [default])
        if isinstance(values, list) and len(values) > 0:
            val = int(values[0])
        else:
            val = int(values)
        return max(min_val, min(val, max_val))
    except (ValueError, IndexError, TypeError):
        return default


def parse_float_param(
    query: Dict[str, list],
    key: str,
    default: float,
    min_val: float = 0.0,
    max_val: float = 1.0,
) -> float:
    """Safely parse a float query parameter with bounds checking.

    Args:
        query: Query dict from parse_qs (values are lists)
        key: Parameter name
        default: Default value if missing or invalid
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Parsed float clamped to [min_val, max_val], or default on error
    """
    try:
        values = query.get(key, [default])
        if isinstance(values, list) and len(values) > 0:
            val = float(values[0])
        else:
            val = float(values)
        return max(min_val, min(val, max_val))
    except (ValueError, IndexError, TypeError):
        return default


def parse_bool_param(
    query: Dict[str, list],
    key: str,
    default: bool = False,
) -> bool:
    """Safely parse a boolean query parameter.

    Recognizes: "true", "1", "yes" as True; "false", "0", "no" as False.

    Args:
        query: Query dict from parse_qs (values are lists)
        key: Parameter name
        default: Default value if missing or invalid

    Returns:
        Parsed boolean or default
    """
    try:
        values = query.get(key, [])
        if not values:
            return default
        val = values[0].lower() if isinstance(values, list) else str(values).lower()
        if val in ("true", "1", "yes"):
            return True
        if val in ("false", "0", "no"):
            return False
        return default
    except (AttributeError, IndexError, TypeError):
        return default


def parse_string_param(
    query: Dict[str, list],
    key: str,
    default: str = "",
    max_length: int = 500,
    allowed_values: Optional[set] = None,
) -> str:
    """Safely parse a string query parameter with validation.

    Args:
        query: Query dict from parse_qs (values are lists)
        key: Parameter name
        default: Default value if missing or invalid
        max_length: Maximum string length (truncates if exceeded)
        allowed_values: Optional set of allowed values (returns default if not in set)

    Returns:
        Parsed and validated string, or default
    """
    try:
        values = query.get(key, [default])
        if isinstance(values, list) and len(values) > 0:
            val = str(values[0])[:max_length]
        else:
            val = str(values)[:max_length]

        if allowed_values is not None and val not in allowed_values:
            return default
        return val
    except (IndexError, TypeError):
        return default


# =============================================================================
# Simple Query Value Parsing (for aiohttp-style query dicts)
# =============================================================================
# These functions work with query dicts where .get() returns a single string
# value, as used by aiohttp's MultiDict.

def safe_query_int(
    query: Any,
    key: str,
    default: int,
    min_val: int = 1,
    max_val: int = 100,
) -> int:
    """Safely parse an integer from a query dict with bounds checking.

    Works with both urllib.parse_qs (list values) and aiohttp MultiDict
    (single string values).

    Args:
        query: Query dict (aiohttp MultiDict or parse_qs result)
        key: Parameter name
        default: Default value if missing or invalid
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Parsed integer clamped to bounds, or default on error
    """
    try:
        raw = query.get(key, default)
        # Handle parse_qs list format
        if isinstance(raw, list):
            raw = raw[0] if raw else default
        val = int(raw)
        return max(min_val, min(val, max_val))
    except (ValueError, IndexError, TypeError):
        return default


def safe_query_float(
    query: Any,
    key: str,
    default: float,
    min_val: float = 0.0,
    max_val: float = 1.0,
) -> float:
    """Safely parse a float from a query dict with bounds checking.

    Works with both urllib.parse_qs (list values) and aiohttp MultiDict
    (single string values).

    Args:
        query: Query dict (aiohttp MultiDict or parse_qs result)
        key: Parameter name
        default: Default value if missing or invalid
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Parsed float clamped to bounds, or default on error
    """
    try:
        raw = query.get(key, default)
        # Handle parse_qs list format
        if isinstance(raw, list):
            raw = raw[0] if raw else default
        val = float(raw)
        return max(min_val, min(val, max_val))
    except (ValueError, IndexError, TypeError):
        return default
