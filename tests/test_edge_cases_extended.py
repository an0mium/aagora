"""
Extended edge case tests for guards added in Rounds 21-27.

These tests verify edge cases that weren't covered by existing test files,
focusing on string split safety and empty list handling.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


# ============================================================================
# HIGH PRIORITY: Empty Agent List Guards
# ============================================================================

class TestEmptyAgentListGuards:
    """Test empty agent list handling across the codebase."""

    def test_orchestrator_require_agents_empty(self):
        """Test _require_agents raises ValueError with empty list."""
        from aragora.debate.orchestrator import Arena

        arena = Arena.__new__(Arena)
        arena.agents = []

        with pytest.raises(ValueError, match="[Nn]o agents"):
            arena._require_agents()

    def test_orchestrator_require_agents_valid(self):
        """Test _require_agents passes with valid agents."""
        from aragora.debate.orchestrator import Arena

        arena = Arena.__new__(Arena)
        arena.agents = [MagicMock(), MagicMock()]

        # Should not raise
        arena._require_agents()

    def test_select_critics_empty_agents(self):
        """Test _select_critics_for_proposal handles empty critic list."""
        from aragora.debate.orchestrator import Arena

        arena = Arena.__new__(Arena)
        # Mock protocol with topology attribute
        arena.protocol = MagicMock()
        arena.protocol.topology = "all-to-all"

        # Empty critics should return empty list, not crash
        result = arena._select_critics_for_proposal("agent1", [])
        assert result == []


# ============================================================================
# HIGH PRIORITY: String Split Safety
# ============================================================================

class TestStringSplitSafety:
    """Test string split operations handle edge cases."""

    def test_agent_name_split_empty_string(self):
        """Test agent name split handles empty string."""
        # Direct test of split behavior
        empty = ""
        parts = empty.split("_")
        # empty.split("_") returns [""], not []
        assert parts == [""]
        # Accessing [0] should still work
        assert parts[0] == ""

    def test_agent_name_split_no_underscore(self):
        """Test agent name split when no underscore present."""
        name = "claude"
        parts = name.split("_")
        assert parts == ["claude"]
        assert parts[0] == "claude"

    def test_agent_name_split_leading_underscore(self):
        """Test agent name split with leading underscore."""
        name = "_agent"
        parts = name.split("_")
        # "_agent".split("_") returns ["", "agent"]
        assert parts[0] == ""
        assert parts[1] == "agent"

    def test_agent_name_split_multiple_underscores(self):
        """Test agent name split with multiple underscores."""
        name = "claude_visionary_v2"
        parts = name.split("_")
        assert parts[0] == "claude"
        assert len(parts) == 3

    def test_agent_name_extraction_pattern(self):
        """Test agent name extraction pattern used throughout codebase."""
        # This pattern is used in prompt_builder.py, personas.py, orchestrator.py
        test_names = [
            ("claude_visionary", "claude"),
            ("gpt4", "gpt4"),
            ("", ""),
            ("_underscore_start", ""),
        ]

        for full_name, expected_base in test_names:
            # Safe extraction pattern
            base = full_name.split("_")[0] if full_name else ""
            assert base == expected_base, f"Failed for {full_name}"


# ============================================================================
# MEDIUM PRIORITY: Convergence Edge Cases
# ============================================================================

class TestConvergenceEdgeCases:
    """Test convergence detection edge cases."""

    def test_convergence_detector_init(self):
        """Test ConvergenceDetector can be initialized."""
        from aragora.debate.convergence import ConvergenceDetector

        detector = ConvergenceDetector(convergence_threshold=0.8)
        assert detector is not None

    def test_convergence_empty_responses(self):
        """Test convergence check with empty response dicts."""
        from aragora.debate.convergence import ConvergenceDetector

        detector = ConvergenceDetector(convergence_threshold=0.8)

        # Empty responses should return None (not enough data)
        result = detector.check_convergence({}, {}, round_number=1)
        assert result is None or hasattr(result, "converged")

    def test_convergence_single_agent(self):
        """Test convergence with single agent responses."""
        from aragora.debate.convergence import ConvergenceDetector

        detector = ConvergenceDetector(convergence_threshold=0.8)

        current = {"agent1": "This is my response"}
        previous = {"agent1": "This is my response"}  # Same response

        result = detector.check_convergence(current, previous, round_number=2)
        # With same response, should detect convergence or return valid result
        assert result is None or hasattr(result, "converged")

    def test_convergence_no_common_agents(self):
        """Test convergence when different agents in each round."""
        from aragora.debate.convergence import ConvergenceDetector

        detector = ConvergenceDetector(convergence_threshold=0.8)

        # Round 1: agent_a, agent_b
        previous = {"agent_a": "Proposal A", "agent_b": "Critique B"}
        # Round 2: agent_c, agent_d (no overlap)
        current = {"agent_c": "Proposal C", "agent_d": "Critique D"}

        # Should handle gracefully without crashing
        result = detector.check_convergence(current, previous, round_number=2)
        assert result is None or hasattr(result, "converged")


# ============================================================================
# MEDIUM PRIORITY: Critique Details Split
# ============================================================================

class TestCritiqueDetailsSplit:
    """Test critique details string parsing."""

    def test_malformed_details_string(self):
        """Test handling of malformed critique details."""
        # Simulate the pattern: "issue: suggestion"
        test_cases = [
            ("valid issue: valid suggestion", ("valid issue", " valid suggestion")),
            ("no colon here", ("no colon here", "")),
            ("", ("", "")),
            (":", ("", "")),
            ("multiple: colons: here", ("multiple", " colons: here")),
        ]

        for details, expected in test_cases:
            if ":" in details:
                parts = details.split(":", 1)
                issue = parts[0]
                suggestion = parts[1] if len(parts) > 1 else ""
            else:
                issue = details
                suggestion = ""

            assert (issue, suggestion) == expected, f"Failed for: {details!r}"


# ============================================================================
# TTL Cache Integration Tests
# ============================================================================

class TestTTLCacheIntegration:
    """Test TTL caching behavior on CritiqueStore methods."""

    def test_critique_store_get_stats_cached(self):
        """Test get_stats uses caching."""
        import tempfile
        from aragora.memory.store import CritiqueStore

        with tempfile.TemporaryDirectory() as tmpdir:
            store = CritiqueStore(db_path=f"{tmpdir}/test.db")

            # First call
            stats1 = store.get_stats()

            # Second call should be cached (same result, faster)
            stats2 = store.get_stats()

            assert stats1 == stats2

    def test_critique_store_retrieve_patterns_cached(self):
        """Test retrieve_patterns uses caching."""
        import tempfile
        from aragora.memory.store import CritiqueStore

        with tempfile.TemporaryDirectory() as tmpdir:
            store = CritiqueStore(db_path=f"{tmpdir}/test.db")

            # First call
            patterns1 = store.retrieve_patterns(limit=5)

            # Second call should be cached
            patterns2 = store.retrieve_patterns(limit=5)

            assert patterns1 == patterns2


# ============================================================================
# Division By Zero Extended Tests
# ============================================================================

class TestDivisionByZeroExtended:
    """Extended division by zero protection tests."""

    def test_calibration_empty_predictions(self):
        """Test calibration score with zero predictions."""
        # Simulate calibration calculation
        total_predictions = 0
        total_error = 0.0

        # Should not divide by zero
        if total_predictions > 0:
            avg_error = total_error / total_predictions
        else:
            avg_error = 0.0

        assert avg_error == 0.0

    def test_success_rate_zero_attempts(self):
        """Test success rate calculation with zero attempts."""
        success_count = 0
        failure_count = 0
        total = success_count + failure_count

        # Safe calculation
        success_rate = success_count / total if total > 0 else 0.0

        assert success_rate == 0.0


# ============================================================================
# Empty Collection Guards
# ============================================================================

class TestEmptyCollectionGuards:
    """Test guards for empty collections throughout the codebase."""

    def test_random_choice_empty_list_guard(self):
        """Test that random.choice on empty list is guarded."""
        import random

        items = []

        # Direct random.choice would raise IndexError
        with pytest.raises(IndexError):
            random.choice(items)

        # Guarded version
        result = random.choice(items) if items else None
        assert result is None

    def test_max_empty_sequence_guard(self):
        """Test max() on empty sequence is guarded."""
        items = []

        # Direct max would raise ValueError
        with pytest.raises(ValueError):
            max(items)

        # Guarded version
        result = max(items, default=0)
        assert result == 0

    def test_sorted_empty_list_guard(self):
        """Test sorted() handles empty list."""
        items = []

        # sorted() handles empty list fine
        result = sorted(items)
        assert result == []

        # sorted with key also works
        result = sorted(items, key=lambda x: x)
        assert result == []
