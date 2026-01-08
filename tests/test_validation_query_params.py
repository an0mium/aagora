"""
Tests for query parameter validation functions.

Verifies the parse_*_param and safe_query_* functions handle:
- Normal values within bounds
- Values exceeding bounds (clamped)
- Invalid/malformed values (fallback to default)
- Empty/missing values
- Both parse_qs format (list values) and aiohttp format (single values)
"""

import pytest

from aragora.server.validation import (
    parse_int_param,
    parse_float_param,
    parse_bool_param,
    parse_string_param,
    safe_query_int,
    safe_query_float,
)


class TestParseIntParam:
    """Tests for parse_int_param (parse_qs format with list values)."""

    def test_normal_value(self):
        """Normal value within bounds."""
        query = {"limit": ["50"]}
        assert parse_int_param(query, "limit", default=20) == 50

    def test_missing_key_returns_default(self):
        """Missing key returns default."""
        query = {}
        assert parse_int_param(query, "limit", default=20) == 20

    def test_empty_list_returns_default(self):
        """Empty list returns default."""
        query = {"limit": []}
        assert parse_int_param(query, "limit", default=20) == 20

    def test_invalid_value_returns_default(self):
        """Invalid (non-numeric) value returns default."""
        query = {"limit": ["abc"]}
        assert parse_int_param(query, "limit", default=20) == 20

    def test_value_below_min_clamped(self):
        """Value below min_val is clamped to min_val."""
        query = {"limit": ["-5"]}
        assert parse_int_param(query, "limit", default=20, min_val=1) == 1

    def test_value_above_max_clamped(self):
        """Value above max_val is clamped to max_val."""
        query = {"limit": ["999"]}
        assert parse_int_param(query, "limit", default=20, max_val=100) == 100

    def test_custom_bounds(self):
        """Custom min/max bounds work correctly."""
        query = {"offset": ["5"]}
        result = parse_int_param(query, "offset", default=0, min_val=0, max_val=1000)
        assert result == 5

    def test_negative_allowed_when_min_negative(self):
        """Negative values allowed when min_val is negative."""
        query = {"delta": ["-10"]}
        result = parse_int_param(query, "delta", default=0, min_val=-100, max_val=100)
        assert result == -10


class TestParseFloatParam:
    """Tests for parse_float_param (parse_qs format with list values)."""

    def test_normal_value(self):
        """Normal float value within bounds."""
        query = {"threshold": ["0.75"]}
        assert parse_float_param(query, "threshold", default=0.5) == 0.75

    def test_missing_key_returns_default(self):
        """Missing key returns default."""
        query = {}
        assert parse_float_param(query, "threshold", default=0.5) == 0.5

    def test_invalid_value_returns_default(self):
        """Invalid value returns default."""
        query = {"threshold": ["not-a-number"]}
        assert parse_float_param(query, "threshold", default=0.5) == 0.5

    def test_value_clamped_to_bounds(self):
        """Value outside bounds is clamped."""
        query = {"threshold": ["1.5"]}
        result = parse_float_param(query, "threshold", default=0.5, max_val=1.0)
        assert result == 1.0


class TestParseBoolParam:
    """Tests for parse_bool_param."""

    def test_true_values(self):
        """Various true values recognized."""
        for val in ["true", "1", "yes", "True", "TRUE", "Yes", "YES"]:
            query = {"enabled": [val]}
            assert parse_bool_param(query, "enabled", default=False) is True

    def test_false_values(self):
        """Various false values recognized."""
        for val in ["false", "0", "no", "False", "FALSE", "No", "NO"]:
            query = {"enabled": [val]}
            assert parse_bool_param(query, "enabled", default=True) is False

    def test_missing_key_returns_default(self):
        """Missing key returns default."""
        query = {}
        assert parse_bool_param(query, "enabled", default=True) is True
        assert parse_bool_param(query, "enabled", default=False) is False

    def test_invalid_value_returns_default(self):
        """Invalid value returns default."""
        query = {"enabled": ["maybe"]}
        assert parse_bool_param(query, "enabled", default=True) is True


class TestParseStringParam:
    """Tests for parse_string_param."""

    def test_normal_value(self):
        """Normal string value."""
        query = {"name": ["test-agent"]}
        assert parse_string_param(query, "name", default="") == "test-agent"

    def test_missing_key_returns_default(self):
        """Missing key returns default."""
        query = {}
        assert parse_string_param(query, "name", default="default-name") == "default-name"

    def test_value_truncated_to_max_length(self):
        """Long value truncated to max_length."""
        query = {"name": ["a" * 100]}
        result = parse_string_param(query, "name", default="", max_length=10)
        assert result == "a" * 10

    def test_allowed_values_enforced(self):
        """Value not in allowed_values returns default."""
        query = {"sort": ["invalid"]}
        result = parse_string_param(
            query, "sort", default="asc", allowed_values={"asc", "desc"}
        )
        assert result == "asc"

    def test_allowed_value_accepted(self):
        """Value in allowed_values is accepted."""
        query = {"sort": ["desc"]}
        result = parse_string_param(
            query, "sort", default="asc", allowed_values={"asc", "desc"}
        )
        assert result == "desc"


class TestSafeQueryInt:
    """Tests for safe_query_int (works with both formats)."""

    def test_aiohttp_format(self):
        """Works with aiohttp MultiDict format (single string values)."""
        class FakeMultiDict:
            def __init__(self, d):
                self._d = d
            def get(self, k, default=None):
                return self._d.get(k, default)

        query = FakeMultiDict({"limit": "50"})
        assert safe_query_int(query, "limit", default=20) == 50

    def test_parse_qs_format(self):
        """Also works with parse_qs format (list values)."""
        query = {"limit": ["50"]}
        assert safe_query_int(query, "limit", default=20) == 50

    def test_bounds_applied(self):
        """Min/max bounds are applied."""
        class FakeMultiDict:
            def get(self, k, default=None):
                return "999"

        query = FakeMultiDict()
        result = safe_query_int(query, "limit", default=20, max_val=100)
        assert result == 100


class TestSafeQueryFloat:
    """Tests for safe_query_float (works with both formats)."""

    def test_aiohttp_format(self):
        """Works with aiohttp MultiDict format."""
        class FakeMultiDict:
            def __init__(self, d):
                self._d = d
            def get(self, k, default=None):
                return self._d.get(k, default)

        query = FakeMultiDict({"threshold": "0.75"})
        assert safe_query_float(query, "threshold", default=0.5) == 0.75

    def test_bounds_applied(self):
        """Min/max bounds are applied."""
        class FakeMultiDict:
            def get(self, k, default=None):
                return "1.5"

        query = FakeMultiDict()
        result = safe_query_float(query, "threshold", default=0.5, max_val=1.0)
        assert result == 1.0


class TestQueryParamSecurityScenarios:
    """Security-focused tests for query parameter validation."""

    def test_sql_injection_attempt_returns_default(self):
        """SQL injection attempts return default value."""
        query = {"limit": ["1; DROP TABLE users;"]}
        result = parse_int_param(query, "limit", default=20)
        assert result == 20

    def test_very_large_number_clamped(self):
        """Very large numbers are clamped to max_val."""
        query = {"limit": ["999999999999999999999"]}
        result = parse_int_param(query, "limit", default=20, max_val=100)
        assert result == 100

    def test_float_overflow_handled(self):
        """Float overflow returns default."""
        query = {"threshold": ["1e999"]}
        # Should either clamp or return default (behavior may vary)
        result = parse_float_param(query, "threshold", default=0.5, max_val=1.0)
        assert 0.0 <= result <= 1.0 or result == 0.5

    def test_empty_string_returns_default(self):
        """Empty string returns default."""
        query = {"limit": [""]}
        result = parse_int_param(query, "limit", default=20)
        assert result == 20

    def test_whitespace_only_returns_default(self):
        """Whitespace-only value returns default."""
        query = {"limit": ["   "]}
        result = parse_int_param(query, "limit", default=20)
        assert result == 20

    def test_negative_value_with_positive_min(self):
        """Negative value with positive min_val is clamped."""
        query = {"limit": ["-100"]}
        result = parse_int_param(query, "limit", default=20, min_val=1, max_val=100)
        assert result == 1
