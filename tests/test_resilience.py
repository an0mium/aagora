"""Tests for resilience patterns (circuit breaker)."""

import pytest
import time
from unittest.mock import patch, MagicMock

from aragora.resilience import CircuitBreaker


class TestCircuitBreakerSingleEntity:
    """Tests for CircuitBreaker in single-entity mode."""

    def test_initial_state_is_closed(self):
        """Circuit starts in closed state."""
        cb = CircuitBreaker()
        assert cb.get_status() == "closed"
        assert cb.can_proceed() is True
        assert cb.failures == 0

    def test_failures_increment(self):
        """Failures increment counter."""
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        assert cb.failures == 1
        cb.record_failure()
        assert cb.failures == 2

    def test_opens_after_threshold(self):
        """Circuit opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure()
        assert cb.get_status() == "closed"
        cb.record_failure()
        assert cb.get_status() == "closed"

        opened = cb.record_failure()
        assert opened is True
        assert cb.get_status() == "open"
        assert cb.can_proceed() is False

    def test_success_resets_failures(self):
        """Success resets failure count."""
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.failures == 2

        cb.record_success()
        assert cb.failures == 0

    def test_success_closes_open_circuit(self):
        """Success closes open circuit."""
        cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.1)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open is True

        # Wait for cooldown then try (simulate half-open)
        time.sleep(0.15)
        assert cb.can_proceed() is True

        # Record success - should close
        cb.record_success()
        assert cb.is_open is False
        assert cb.get_status() == "closed"

    def test_cooldown_resets_circuit(self):
        """Circuit resets after cooldown period."""
        cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.1)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.can_proceed() is False

        # Wait for cooldown
        time.sleep(0.15)

        # Should be able to proceed now
        assert cb.can_proceed() is True
        assert cb.get_status() == "closed"

    def test_is_open_property_settable(self):
        """Can manually set is_open for testing."""
        cb = CircuitBreaker()
        assert cb.is_open is False

        cb.is_open = True
        assert cb.is_open is True
        assert cb.get_status() == "open"

        cb.is_open = False
        assert cb.is_open is False
        assert cb.get_status() == "closed"


class TestCircuitBreakerMultiEntity:
    """Tests for CircuitBreaker in multi-entity mode."""

    def test_tracks_entities_independently(self):
        """Each entity has independent failure tracking."""
        cb = CircuitBreaker(failure_threshold=2)

        cb.record_failure("agent-1")
        cb.record_failure("agent-1")

        assert cb.is_available("agent-1") is False
        assert cb.is_available("agent-2") is True

    def test_half_open_success_threshold(self):
        """Entity requires multiple successes to close."""
        cb = CircuitBreaker(
            failure_threshold=2,
            cooldown_seconds=0.01,
            half_open_success_threshold=2,
        )

        # Open circuit for entity
        cb.record_failure("agent-1")
        cb.record_failure("agent-1")
        assert cb.get_status("agent-1") == "open"

        # Wait for cooldown
        time.sleep(0.02)
        assert cb.get_status("agent-1") == "half-open"

        # First success doesn't close
        cb.record_success("agent-1")
        assert cb.get_status("agent-1") == "half-open"

        # Second success closes
        cb.record_success("agent-1")
        assert cb.get_status("agent-1") == "closed"

    def test_filter_available_entities(self):
        """Filters out entities with open circuits."""
        cb = CircuitBreaker(failure_threshold=2)

        # Open circuit for agent-1
        cb.record_failure("agent-1")
        cb.record_failure("agent-1")

        entities = ["agent-1", "agent-2", "agent-3"]
        available = cb.filter_available_entities(entities)

        assert "agent-1" not in available
        assert "agent-2" in available
        assert "agent-3" in available

    def test_filter_available_agents_with_objects(self):
        """Works with objects that have .name attribute."""
        cb = CircuitBreaker(failure_threshold=2)

        # Open circuit for agent-1
        cb.record_failure("agent-1")
        cb.record_failure("agent-1")

        class MockAgent:
            def __init__(self, name):
                self.name = name

        agents = [MockAgent("agent-1"), MockAgent("agent-2")]
        available = cb.filter_available_agents(agents)

        assert len(available) == 1
        assert available[0].name == "agent-2"


class TestCircuitBreakerPersistence:
    """Tests for CircuitBreaker serialization."""

    def test_to_dict(self):
        """Can serialize to dict."""
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure()
        cb.record_failure("entity-1")

        data = cb.to_dict()

        assert "single_mode" in data
        assert data["single_mode"]["failures"] == 1
        assert "entity_mode" in data
        assert data["entity_mode"]["failures"]["entity-1"] == 1

    def test_from_dict(self):
        """Can restore from dict."""
        data = {
            "entity_mode": {
                "failures": {"agent-1": 2, "agent-2": 1},
                "open_circuits": {"agent-1": 5.0},  # 5 seconds elapsed
            }
        }

        cb = CircuitBreaker.from_dict(data, failure_threshold=3, cooldown_seconds=10)

        assert cb._failures["agent-1"] == 2
        assert cb._failures["agent-2"] == 1
        # agent-1 should still be in cooldown (5s < 10s)
        assert cb.is_available("agent-1") is False

    def test_from_dict_expired_cooldown(self):
        """Expired cooldowns are not restored."""
        data = {
            "entity_mode": {
                "failures": {"agent-1": 3},
                "open_circuits": {"agent-1": 120.0},  # 120 seconds elapsed
            }
        }

        cb = CircuitBreaker.from_dict(data, cooldown_seconds=60)

        # agent-1 cooldown expired, should be available
        # (but note failures are restored, so next failure may re-open)
        assert cb.is_available("agent-1") is True


class TestCircuitBreakerReset:
    """Tests for CircuitBreaker reset functionality."""

    def test_reset_all(self):
        """Reset clears all state."""
        cb = CircuitBreaker(failure_threshold=2)

        # Build up some state
        cb.record_failure()
        cb.record_failure("agent-1")
        cb.record_failure("agent-1")

        cb.reset()

        assert cb.failures == 0
        assert cb.is_open is False
        assert cb._failures == {}
        assert cb._circuit_open_at == {}

    def test_reset_single_entity(self):
        """Can reset single entity."""
        cb = CircuitBreaker(failure_threshold=2)

        cb.record_failure("agent-1")
        cb.record_failure("agent-1")
        cb.record_failure("agent-2")
        cb.record_failure("agent-2")

        cb.reset("agent-1")

        # agent-1 reset, agent-2 still open
        assert cb.is_available("agent-1") is True
        assert cb.is_available("agent-2") is False


class TestCircuitBreakerStatus:
    """Tests for status reporting."""

    def test_get_all_status(self):
        """Gets status for all tracked entities."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure("agent-1")
        cb.record_failure("agent-2")
        cb.record_failure("agent-2")
        cb.record_failure("agent-2")

        status = cb.get_all_status()

        assert status["agent-1"]["status"] == "closed"
        assert status["agent-1"]["failures"] == 1
        assert status["agent-2"]["status"] == "open"
        assert status["agent-2"]["failures"] == 3

    def test_reset_timeout_alias(self):
        """reset_timeout is alias for cooldown_seconds."""
        cb = CircuitBreaker(cooldown_seconds=45.0)
        assert cb.reset_timeout == 45.0
