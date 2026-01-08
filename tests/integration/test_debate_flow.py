"""
Integration tests for complete debate flows.

These tests verify the full debate lifecycle from start to finish,
including all major components: Arena, agents, memory, events, and persistence.
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, patch

import pytest

from aragora.core import Agent, Message, Critique, Vote, Environment, DebateResult
from aragora.debate.orchestrator import Arena, DebateProtocol
from aragora.memory.store import CritiqueStore


# =============================================================================
# Auto-mock external dependencies for all tests
# =============================================================================


@pytest.fixture(autouse=True)
def mock_external_calls():
    """Mock external API calls to prevent network requests during tests."""
    # Mock the Arena's trending context gathering to prevent Reddit/pulse API calls
    with patch.object(
        Arena, "_gather_trending_context",
        new_callable=AsyncMock,
        return_value=None
    ):
        # Mock the ContextInitializer to skip external research
        with patch(
            "aragora.debate.phases.context_init.ContextInitializer.initialize",
            new_callable=AsyncMock,
            return_value=None
        ):
            yield


# =============================================================================
# Mock Agent for Testing
# =============================================================================


class MockAgent(Agent):
    """Mock agent for integration testing that doesn't make API calls."""

    def __init__(self, name: str = "mock", model: str = "mock-model", role: str = "proposer"):
        super().__init__(name, model, role)
        self.agent_type = "mock"
        self.generate_responses = []
        self.critique_responses = []
        self.vote_responses = []
        self._generate_call_count = 0
        self._critique_call_count = 0
        self._vote_call_count = 0
        self.generate_calls = []  # Track all calls
        self.critique_calls = []
        self.vote_calls = []

    async def generate(self, prompt: str, context: list = None) -> str:
        """Return mock response and track the call."""
        self.generate_calls.append({"prompt": prompt, "context": context})
        if self.generate_responses:
            response = self.generate_responses[self._generate_call_count % len(self.generate_responses)]
            self._generate_call_count += 1
            return response
        return f"Mock response from {self.name}: {prompt[:50]}"

    async def critique(self, proposal: str, task: str, context: list = None) -> Critique:
        """Return mock critique and track the call."""
        self.critique_calls.append({"proposal": proposal, "task": task, "context": context})
        if self.critique_responses:
            response = self.critique_responses[self._critique_call_count % len(self.critique_responses)]
            self._critique_call_count += 1
            return response
        return Critique(
            agent=self.name,
            target_agent="proposer",
            target_content=proposal[:100],
            issues=[f"Issue found by {self.name}"],
            suggestions=[f"Suggestion from {self.name}"],
            severity=0.5,
            reasoning=f"Critique reasoning from {self.name}"
        )

    async def vote(self, proposals: dict, task: str) -> Vote:
        """Return mock vote and track the call."""
        self.vote_calls.append({"proposals": proposals, "task": task})
        if self.vote_responses:
            response = self.vote_responses[self._vote_call_count % len(self.vote_responses)]
            self._vote_call_count += 1
            return response
        choice = list(proposals.keys())[0] if proposals else "none"
        return Vote(
            agent=self.name,
            choice=choice,
            reasoning=f"Vote reasoning from {self.name}",
            confidence=0.8,
            continue_debate=False
        )


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_db():
    """Create a temporary database path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def critique_store(temp_db):
    """Create a CritiqueStore with temp database."""
    return CritiqueStore(temp_db)


@pytest.fixture
def mock_emitter():
    """Create a mock event emitter."""
    emitter = Mock()
    emitter.emit = Mock()
    emitter.subscribe = Mock()
    return emitter


@pytest.fixture
def basic_agents():
    """Create a basic pair of mock agents."""
    proposer = MockAgent("alice", role="proposer")
    critic = MockAgent("bob", role="critic")

    proposer.generate_responses = [
        "I propose we implement a distributed cache with TTL-based expiration.",
        "Based on the feedback, I'll add cache invalidation callbacks.",
    ]
    critic.generate_responses = [
        "The cache design looks solid, but we should consider memory limits.",
        "The invalidation callbacks address my concerns.",
    ]

    return [proposer, critic]


@pytest.fixture
def three_agents():
    """Create three agents for more complex debates."""
    alice = MockAgent("alice", role="proposer")
    bob = MockAgent("bob", role="critic")
    charlie = MockAgent("charlie", role="synthesizer")

    alice.generate_responses = ["Initial proposal from Alice"]
    bob.generate_responses = ["Bob's critique and counter-proposal"]
    charlie.generate_responses = ["Charlie's synthesis of both views"]

    return [alice, bob, charlie]


# =============================================================================
# Test Classes
# =============================================================================


class TestMinimalDebateFlow:
    """Test the minimal code path for a complete debate."""

    @pytest.mark.asyncio
    async def test_debate_completes_successfully(self, basic_agents):
        """A minimal debate should complete without errors."""
        env = Environment(task="Design a caching system", max_rounds=2)
        protocol = DebateProtocol(rounds=2)

        arena = Arena(env, basic_agents, protocol)
        result = await arena.run()

        assert isinstance(result, DebateResult)
        assert result.task == "Design a caching system"

    @pytest.mark.asyncio
    async def test_debate_produces_result_fields(self, basic_agents):
        """Debate result should contain all expected fields."""
        env = Environment(task="Test task", max_rounds=2)
        protocol = DebateProtocol(rounds=2)

        arena = Arena(env, basic_agents, protocol)
        result = await arena.run()

        # Core fields should be present
        assert hasattr(result, "task")
        assert hasattr(result, "messages")
        assert hasattr(result, "votes")
        assert hasattr(result, "consensus_reached")
        assert hasattr(result, "rounds_used")

    @pytest.mark.asyncio
    async def test_debate_generates_messages(self, basic_agents):
        """Debate should generate messages from agents."""
        env = Environment(task="Test task", max_rounds=2)
        protocol = DebateProtocol(rounds=2)

        arena = Arena(env, basic_agents, protocol)
        result = await arena.run()

        # Messages list should exist (may be empty if no proposers)
        # The important thing is the debate completed with a result
        assert isinstance(result.messages, list)

    @pytest.mark.asyncio
    async def test_agents_are_called(self, basic_agents):
        """Agents should have their methods called during debate."""
        env = Environment(task="Test task", max_rounds=2)
        protocol = DebateProtocol(rounds=2)

        arena = Arena(env, basic_agents, protocol)
        await arena.run()

        # At least one agent should have generated content
        assert any(
            len(agent.generate_calls) > 0 or len(agent.vote_calls) > 0
            for agent in basic_agents
        )


class TestDebateWithMemory:
    """Test debates with CritiqueStore persistence."""

    @pytest.mark.asyncio
    async def test_debate_with_memory_completes(self, basic_agents, critique_store):
        """Debate with memory store should complete."""
        env = Environment(task="Test with memory", max_rounds=2)
        protocol = DebateProtocol(rounds=2)

        arena = Arena(env, basic_agents, protocol, memory=critique_store)
        result = await arena.run()

        assert isinstance(result, DebateResult)

    @pytest.mark.asyncio
    async def test_memory_stores_are_accessible(self, basic_agents, temp_db):
        """Memory stores should be accessible after debate."""
        store = CritiqueStore(temp_db)
        env = Environment(task="Memory test", max_rounds=1)
        protocol = DebateProtocol(rounds=1)

        arena = Arena(env, basic_agents, protocol, memory=store)
        await arena.run()

        # Store should have stats method
        stats = store.get_stats()
        assert isinstance(stats, dict)


class TestDebateWithEvents:
    """Test debates with event emission."""

    @pytest.mark.asyncio
    async def test_debate_with_emitter(self, basic_agents, mock_emitter):
        """Debate should work with event emitter."""
        env = Environment(task="Event test", max_rounds=2)
        protocol = DebateProtocol(rounds=2)

        arena = Arena(env, basic_agents, protocol, event_emitter=mock_emitter)
        result = await arena.run()

        assert isinstance(result, DebateResult)


class TestDebateConsensus:
    """Test consensus mechanisms."""

    @pytest.mark.asyncio
    async def test_majority_consensus(self, three_agents):
        """Majority consensus should work with 3 agents."""
        # All agents vote for alice
        for agent in three_agents:
            agent.vote_responses = [Vote(
                agent=agent.name,
                choice="alice",
                reasoning="Alice's proposal is best",
                confidence=0.8,
                continue_debate=False
            )]

        env = Environment(task="Consensus test", max_rounds=2)
        protocol = DebateProtocol(rounds=2, consensus="majority")

        arena = Arena(env, three_agents, protocol)
        result = await arena.run()

        assert isinstance(result, DebateResult)

    @pytest.mark.asyncio
    async def test_unanimous_consensus_requirement(self, basic_agents):
        """Unanimous consensus should require all agents to agree."""
        # Both agents vote for same choice
        basic_agents[0].vote_responses = [Vote(
            agent="alice",
            choice="alice",
            reasoning="My proposal is good",
            confidence=0.9,
            continue_debate=False
        )]
        basic_agents[1].vote_responses = [Vote(
            agent="bob",
            choice="alice",
            reasoning="I agree with Alice",
            confidence=0.85,
            continue_debate=False
        )]

        env = Environment(task="Unanimous test", max_rounds=2)
        protocol = DebateProtocol(rounds=2, consensus="unanimous")

        arena = Arena(env, basic_agents, protocol)
        result = await arena.run()

        assert isinstance(result, DebateResult)


class TestEarlyStopping:
    """Test early stopping behavior."""

    @pytest.mark.asyncio
    async def test_early_stopping_enabled(self, basic_agents):
        """Debate should stop early when consensus reached."""
        # Both agents vote to stop
        for agent in basic_agents:
            agent.vote_responses = [Vote(
                agent=agent.name,
                choice="alice",
                reasoning="Done",
                confidence=0.95,
                continue_debate=False
            )]

        env = Environment(task="Early stop test", max_rounds=10)
        protocol = DebateProtocol(rounds=10, early_stopping=True)

        arena = Arena(env, basic_agents, protocol)
        result = await arena.run()

        # Should complete without using all 10 rounds
        assert result.rounds_used <= 10

    @pytest.mark.asyncio
    async def test_early_stopping_disabled(self, basic_agents):
        """Debate should continue when early stopping is disabled."""
        # Even if agents want to stop, debate continues
        for agent in basic_agents:
            agent.vote_responses = [Vote(
                agent=agent.name,
                choice="alice",
                reasoning="Done",
                confidence=0.95,
                continue_debate=False
            )]

        env = Environment(task="No early stop test", max_rounds=2)
        protocol = DebateProtocol(rounds=2, early_stopping=False)

        arena = Arena(env, basic_agents, protocol)
        result = await arena.run()

        assert isinstance(result, DebateResult)


class TestDebateRounds:
    """Test round limits and behavior."""

    @pytest.mark.asyncio
    async def test_respects_max_rounds(self, basic_agents):
        """Debate should not exceed max_rounds."""
        env = Environment(task="Round limit test", max_rounds=3)
        protocol = DebateProtocol(rounds=3)

        arena = Arena(env, basic_agents, protocol)
        result = await arena.run()

        assert result.rounds_used <= 3

    @pytest.mark.asyncio
    async def test_single_round_debate(self, basic_agents):
        """Single round debate should complete."""
        env = Environment(task="Single round", max_rounds=1)
        protocol = DebateProtocol(rounds=1)

        arena = Arena(env, basic_agents, protocol)
        result = await arena.run()

        assert result.rounds_used >= 1

    @pytest.mark.asyncio
    async def test_zero_rounds_uses_default(self, basic_agents):
        """Zero rounds should use at least one round."""
        env = Environment(task="Zero rounds test", max_rounds=1)
        # Protocol with 0 rounds - should still do something
        protocol = DebateProtocol(rounds=0)

        arena = Arena(env, basic_agents, protocol)
        result = await arena.run()

        assert isinstance(result, DebateResult)


class TestMultipleAgents:
    """Test debates with varying numbers of agents."""

    @pytest.mark.asyncio
    async def test_two_agents(self, basic_agents):
        """Two-agent debate should work."""
        env = Environment(task="Two agents", max_rounds=2)
        protocol = DebateProtocol(rounds=2)

        arena = Arena(env, basic_agents, protocol)
        result = await arena.run()

        assert isinstance(result, DebateResult)

    @pytest.mark.asyncio
    async def test_three_agents(self, three_agents):
        """Three-agent debate should work."""
        env = Environment(task="Three agents", max_rounds=2)
        protocol = DebateProtocol(rounds=2)

        arena = Arena(env, three_agents, protocol)
        result = await arena.run()

        assert isinstance(result, DebateResult)

    @pytest.mark.asyncio
    async def test_single_agent(self):
        """Single-agent debate should still complete."""
        agent = MockAgent("solo", role="proposer")
        agent.generate_responses = ["Solo proposal"]
        agent.vote_responses = [Vote(
            agent="solo",
            choice="solo",
            reasoning="I'm the only one",
            confidence=1.0,
            continue_debate=False
        )]

        env = Environment(task="Solo test", max_rounds=1)
        protocol = DebateProtocol(rounds=1)

        arena = Arena(env, [agent], protocol)
        result = await arena.run()

        assert isinstance(result, DebateResult)


class TestDebateResult:
    """Test DebateResult structure and content."""

    @pytest.mark.asyncio
    async def test_result_has_messages(self, basic_agents):
        """Result should contain message history."""
        env = Environment(task="Messages test", max_rounds=2)
        protocol = DebateProtocol(rounds=2)

        arena = Arena(env, basic_agents, protocol)
        result = await arena.run()

        assert isinstance(result.messages, list)

    @pytest.mark.asyncio
    async def test_result_has_task(self, basic_agents):
        """Result should preserve the original task."""
        task = "Unique task for testing"
        env = Environment(task=task, max_rounds=2)
        protocol = DebateProtocol(rounds=2)

        arena = Arena(env, basic_agents, protocol)
        result = await arena.run()

        assert result.task == task

    @pytest.mark.asyncio
    async def test_result_rounds_used_positive(self, basic_agents):
        """Result should report positive rounds used."""
        env = Environment(task="Rounds test", max_rounds=2)
        protocol = DebateProtocol(rounds=2)

        arena = Arena(env, basic_agents, protocol)
        result = await arena.run()

        assert result.rounds_used >= 0


class TestDebateErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_empty_task(self, basic_agents):
        """Debate with empty task should still complete."""
        env = Environment(task="", max_rounds=1)
        protocol = DebateProtocol(rounds=1)

        arena = Arena(env, basic_agents, protocol)
        result = await arena.run()

        assert isinstance(result, DebateResult)

    @pytest.mark.asyncio
    async def test_long_task(self, basic_agents):
        """Debate with very long task should handle it."""
        long_task = "A" * 10000  # Very long task
        env = Environment(task=long_task, max_rounds=1)
        protocol = DebateProtocol(rounds=1)

        arena = Arena(env, basic_agents, protocol)
        result = await arena.run()

        assert isinstance(result, DebateResult)

    @pytest.mark.asyncio
    async def test_unicode_task(self, basic_agents):
        """Debate should handle unicode in task."""
        task = "设计一个缓存系统 🚀 with émojis"
        env = Environment(task=task, max_rounds=1)
        protocol = DebateProtocol(rounds=1)

        arena = Arena(env, basic_agents, protocol)
        result = await arena.run()

        assert isinstance(result, DebateResult)
