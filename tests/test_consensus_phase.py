"""
Tests for aragora.debate.phases.consensus_phase module.

Tests ConsensusPhase class and voting/consensus resolution.
"""

import pytest
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional
from unittest.mock import MagicMock, AsyncMock

from aragora.debate.context import DebateContext
from aragora.debate.phases.consensus_phase import ConsensusPhase


# ============================================================================
# Mock Classes
# ============================================================================

@dataclass
class MockEnvironment:
    """Mock environment for testing."""
    task: str = "Test task"
    context: str = ""


@dataclass
class MockAgent:
    """Mock agent for testing."""
    name: str = "test_agent"
    role: str = "proposer"
    stance: Optional[str] = None


@dataclass
class MockVote:
    """Mock vote for testing."""
    agent: str = "test_agent"
    choice: str = "proposal_a"
    confidence: float = 0.8
    reasoning: str = "Good proposal"


@dataclass
class MockDebateResult:
    """Mock debate result for testing."""
    id: str = "debate_001"
    votes: list = field(default_factory=list)
    critiques: list = field(default_factory=list)
    messages: list = field(default_factory=list)
    final_answer: str = ""
    consensus_reached: bool = False
    confidence: float = 0.0
    consensus_strength: str = ""
    consensus_variance: float = 0.0
    dissenting_views: list = field(default_factory=list)
    rounds_used: int = 0
    debate_cruxes: list = field(default_factory=list)
    evidence_suggestions: list = field(default_factory=list)


@dataclass
class MockProtocol:
    """Mock protocol for testing."""
    consensus: str = "majority"
    consensus_threshold: float = 0.5
    user_vote_weight: float = 0.5
    rounds: int = 3
    judge_selection: str = "random"


# ============================================================================
# ConsensusPhase Construction Tests
# ============================================================================

class TestConsensusPhaseConstruction:
    """Tests for ConsensusPhase construction."""

    def test_minimal_construction(self):
        """Should create with no arguments."""
        phase = ConsensusPhase()
        assert phase.protocol is None
        assert phase.hooks == {}

    def test_full_construction(self):
        """Should create with all arguments."""
        protocol = MockProtocol()
        hooks = {"on_vote": MagicMock()}

        phase = ConsensusPhase(
            protocol=protocol,
            elo_system=MagicMock(),
            memory=MagicMock(),
            hooks=hooks,
        )

        assert phase.protocol is protocol
        assert "on_vote" in phase.hooks


# ============================================================================
# None Consensus Mode Tests
# ============================================================================

class TestNoneConsensusMode:
    """Tests for 'none' consensus mode."""

    @pytest.mark.asyncio
    async def test_none_mode_combines_proposals(self):
        """Should combine all proposals without voting."""
        protocol = MockProtocol(consensus="none")
        phase = ConsensusPhase(protocol=protocol)

        ctx = DebateContext(env=MockEnvironment())
        ctx.proposals = {"claude": "Proposal A", "gpt4": "Proposal B"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        assert "[claude]" in ctx.result.final_answer
        assert "[gpt4]" in ctx.result.final_answer
        assert ctx.result.consensus_reached is False
        assert ctx.result.confidence == 0.5


# ============================================================================
# Majority Consensus Mode Tests
# ============================================================================

class TestMajorityConsensusMode:
    """Tests for 'majority' consensus mode."""

    @pytest.mark.asyncio
    async def test_majority_voting(self):
        """Should collect votes and determine majority winner."""
        protocol = MockProtocol(consensus="majority", consensus_threshold=0.5)

        async def vote_with_agent(agent, proposals, task):
            return MockVote(agent=agent.name, choice="claude", confidence=0.8)

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=vote_with_agent,
            group_similar_votes=lambda votes: {"claude": ["claude"]},
        )

        agents = [MockAgent(name="claude"), MockAgent(name="gpt4")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A", "gpt4": "Proposal B"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        assert ctx.result.consensus_reached is True
        assert ctx.result.confidence == 1.0  # All votes for same choice

    @pytest.mark.asyncio
    async def test_majority_no_consensus(self):
        """Should detect when consensus threshold not met."""
        protocol = MockProtocol(consensus="majority", consensus_threshold=0.8)

        vote_idx = [0]
        async def vote_with_agent(agent, proposals, task):
            vote_idx[0] += 1
            if vote_idx[0] == 1:
                return MockVote(agent=agent.name, choice="claude", confidence=0.8)
            return MockVote(agent=agent.name, choice="gpt4", confidence=0.7)

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=vote_with_agent,
            group_similar_votes=lambda votes: {"claude": ["claude"], "gpt4": ["gpt4"]},
        )

        agents = [MockAgent(name="claude"), MockAgent(name="gpt4")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A", "gpt4": "Proposal B"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        assert ctx.result.consensus_reached is False
        assert ctx.result.confidence == 0.5  # 50% for winner

    @pytest.mark.asyncio
    async def test_weighted_voting(self):
        """Should apply vote weights from various sources."""
        protocol = MockProtocol(consensus="majority")

        async def vote_with_agent(agent, proposals, task):
            return MockVote(agent=agent.name, choice="claude", confidence=0.8)

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=vote_with_agent,
            agent_weights={"claude": 0.5, "gpt4": 1.5},
            group_similar_votes=lambda votes: {"claude": ["claude"]},
        )

        agents = [MockAgent(name="claude"), MockAgent(name="gpt4")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        # Should have applied weights
        assert ctx.result.consensus_reached is True

    @pytest.mark.asyncio
    async def test_emit_vote_hook(self):
        """Should emit on_vote hook for each vote."""
        protocol = MockProtocol(consensus="majority")
        on_vote = MagicMock()

        async def vote_with_agent(agent, proposals, task):
            return MockVote(agent=agent.name, choice="claude", confidence=0.8)

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=vote_with_agent,
            hooks={"on_vote": on_vote},
            group_similar_votes=lambda votes: {"claude": ["claude"]},
        )

        agents = [MockAgent(name="claude")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        on_vote.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_vote_to_recorder(self):
        """Should record votes to recorder."""
        protocol = MockProtocol(consensus="majority")
        recorder = MagicMock()

        async def vote_with_agent(agent, proposals, task):
            return MockVote(agent=agent.name, choice="claude", confidence=0.8)

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=vote_with_agent,
            recorder=recorder,
            group_similar_votes=lambda votes: {"claude": ["claude"]},
        )

        agents = [MockAgent(name="claude")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        recorder.record_vote.assert_called_once()


# ============================================================================
# Unanimous Consensus Mode Tests
# ============================================================================

class TestUnanimousConsensusMode:
    """Tests for 'unanimous' consensus mode."""

    @pytest.mark.asyncio
    async def test_unanimous_success(self):
        """Should detect unanimous consensus."""
        protocol = MockProtocol(consensus="unanimous")

        async def vote_with_agent(agent, proposals, task):
            return MockVote(agent=agent.name, choice="claude", confidence=0.9)

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=vote_with_agent,
            group_similar_votes=lambda votes: {"claude": ["claude"]},
        )

        agents = [MockAgent(name="claude"), MockAgent(name="gpt4")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        assert ctx.result.consensus_reached is True
        assert ctx.result.consensus_strength == "unanimous"

    @pytest.mark.asyncio
    async def test_unanimous_failure(self):
        """Should detect when unanimity not achieved."""
        protocol = MockProtocol(consensus="unanimous")

        vote_idx = [0]
        async def vote_with_agent(agent, proposals, task):
            vote_idx[0] += 1
            if vote_idx[0] == 1:
                return MockVote(agent=agent.name, choice="claude", confidence=0.8)
            return MockVote(agent=agent.name, choice="gpt4", confidence=0.8)

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=vote_with_agent,
            group_similar_votes=lambda votes: {"claude": ["claude"], "gpt4": ["gpt4"]},
        )

        agents = [MockAgent(name="claude"), MockAgent(name="gpt4")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A", "gpt4": "Proposal B"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        assert ctx.result.consensus_reached is False
        assert ctx.result.consensus_strength == "none"
        assert "[No unanimous consensus reached]" in ctx.result.final_answer

    @pytest.mark.asyncio
    async def test_unanimous_with_voting_errors(self):
        """Should count voting errors as dissent."""
        protocol = MockProtocol(consensus="unanimous")

        async def vote_with_agent(agent, proposals, task):
            if agent.name == "gpt4":
                raise Exception("Vote error")
            return MockVote(agent=agent.name, choice="claude", confidence=0.9)

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=vote_with_agent,
            group_similar_votes=lambda votes: {"claude": ["claude"]},
        )

        agents = [MockAgent(name="claude"), MockAgent(name="gpt4")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        # Error counts as dissent, so not unanimous
        assert ctx.result.consensus_reached is False


# ============================================================================
# Judge Consensus Mode Tests
# ============================================================================

class TestJudgeConsensusMode:
    """Tests for 'judge' consensus mode."""

    @pytest.mark.asyncio
    async def test_judge_synthesis(self):
        """Should use judge to synthesize final answer."""
        protocol = MockProtocol(consensus="judge", judge_selection="random")

        judge = MockAgent(name="judge_claude", role="judge")

        phase = ConsensusPhase(
            protocol=protocol,
            select_judge=AsyncMock(return_value=judge),
            build_judge_prompt=MagicMock(return_value="Synthesize these proposals"),
            generate_with_agent=AsyncMock(return_value="Synthesized answer"),
        )

        agents = [MockAgent(name="claude"), MockAgent(name="gpt4")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A", "gpt4": "Proposal B"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        assert ctx.result.final_answer == "Synthesized answer"
        assert ctx.result.consensus_reached is True
        assert ctx.result.confidence == 0.8

    @pytest.mark.asyncio
    async def test_judge_error_fallback(self):
        """Should fall back to first proposal on judge error."""
        protocol = MockProtocol(consensus="judge")

        judge = MockAgent(name="judge_claude", role="judge")

        phase = ConsensusPhase(
            protocol=protocol,
            select_judge=AsyncMock(return_value=judge),
            build_judge_prompt=MagicMock(return_value="Synthesize"),
            generate_with_agent=AsyncMock(side_effect=Exception("Judge error")),
        )

        agents = [MockAgent(name="claude")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Fallback proposal"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        assert ctx.result.final_answer == "Fallback proposal"
        assert ctx.result.consensus_reached is False

    @pytest.mark.asyncio
    async def test_emit_judge_selected_hook(self):
        """Should emit on_judge_selected hook."""
        protocol = MockProtocol(consensus="judge", judge_selection="voted")
        on_judge = MagicMock()

        judge = MockAgent(name="judge_claude", role="judge")

        phase = ConsensusPhase(
            protocol=protocol,
            select_judge=AsyncMock(return_value=judge),
            build_judge_prompt=MagicMock(return_value="Synthesize"),
            generate_with_agent=AsyncMock(return_value="Answer"),
            hooks={"on_judge_selected": on_judge},
        )

        ctx = DebateContext(env=MockEnvironment(), agents=[])
        ctx.proposals = {"claude": "Proposal"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        on_judge.assert_called_once_with("judge_claude", "voted")


# ============================================================================
# Vote Grouping Tests
# ============================================================================

class TestVoteGrouping:
    """Tests for vote grouping and choice mapping."""

    @pytest.mark.asyncio
    async def test_group_similar_votes(self):
        """Should group similar vote choices."""
        protocol = MockProtocol(consensus="majority")

        async def vote_with_agent(agent, proposals, task):
            return MockVote(agent=agent.name, choice="Claude's proposal", confidence=0.8)

        def group_similar(votes):
            return {"claude": ["claude", "Claude's proposal"]}

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=vote_with_agent,
            group_similar_votes=group_similar,
        )

        agents = [MockAgent(name="claude")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        # Vote should be counted under canonical choice
        assert ctx.result.consensus_reached is True


# ============================================================================
# User Vote Tests
# ============================================================================

class TestUserVotes:
    """Tests for user vote handling."""

    @pytest.mark.asyncio
    async def test_include_user_votes(self):
        """Should include user votes in majority count."""
        protocol = MockProtocol(consensus="majority", user_vote_weight=0.5)

        async def vote_with_agent(agent, proposals, task):
            return MockVote(agent=agent.name, choice="gpt4", confidence=0.8)

        user_votes = [{"choice": "claude", "user_id": "user1", "intensity": 5}]

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=vote_with_agent,
            user_votes=user_votes,
            drain_user_events=MagicMock(),
            group_similar_votes=lambda votes: {"claude": ["claude"], "gpt4": ["gpt4"]},
        )

        agents = [MockAgent(name="gpt4")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A", "gpt4": "Proposal B"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        # User vote should be counted (with weight 0.5)
        assert "claude" in ctx.vote_tally or "gpt4" in ctx.vote_tally


# ============================================================================
# Calibration Tracker Tests
# ============================================================================

class TestCalibrationTracking:
    """Tests for calibration prediction tracking."""

    @pytest.mark.asyncio
    async def test_record_calibration_predictions(self):
        """Should record calibration predictions."""
        protocol = MockProtocol(consensus="majority")
        calibration = MagicMock()

        async def vote_with_agent(agent, proposals, task):
            return MockVote(agent=agent.name, choice="claude", confidence=0.9)

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=vote_with_agent,
            calibration_tracker=calibration,
            extract_debate_domain=lambda: "test_domain",
            group_similar_votes=lambda votes: {"claude": ["claude"]},
        )

        agents = [MockAgent(name="claude")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        calibration.record_prediction.assert_called_once()


# ============================================================================
# Position Tracker Tests
# ============================================================================

class TestPositionTracking:
    """Tests for position tracker integration."""

    @pytest.mark.asyncio
    async def test_record_vote_position(self):
        """Should record vote position."""
        protocol = MockProtocol(consensus="majority")
        position_tracker = MagicMock()

        async def vote_with_agent(agent, proposals, task):
            return MockVote(agent=agent.name, choice="claude", confidence=0.8)

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=vote_with_agent,
            position_tracker=position_tracker,
            group_similar_votes=lambda votes: {"claude": ["claude"]},
        )

        agents = [MockAgent(name="claude")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        position_tracker.record_position.assert_called()

    @pytest.mark.asyncio
    async def test_finalize_debate_position(self):
        """Should finalize debate for position tracker."""
        protocol = MockProtocol(consensus="majority")
        position_tracker = MagicMock()

        async def vote_with_agent(agent, proposals, task):
            return MockVote(agent=agent.name, choice="claude", confidence=0.8)

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=vote_with_agent,
            position_tracker=position_tracker,
            group_similar_votes=lambda votes: {"claude": ["claude"]},
        )

        agents = [MockAgent(name="claude")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        position_tracker.finalize_debate.assert_called_once()


# ============================================================================
# Spectator Notification Tests
# ============================================================================

class TestSpectatorNotifications:
    """Tests for spectator notifications."""

    @pytest.mark.asyncio
    async def test_notify_spectator_on_vote(self):
        """Should notify spectator of votes."""
        protocol = MockProtocol(consensus="majority")
        notify = MagicMock()

        async def vote_with_agent(agent, proposals, task):
            return MockVote(agent=agent.name, choice="claude", confidence=0.8)

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=vote_with_agent,
            notify_spectator=notify,
            group_similar_votes=lambda votes: {"claude": ["claude"]},
        )

        agents = [MockAgent(name="claude")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        # Should be called for vote and consensus
        assert notify.call_count >= 2

    @pytest.mark.asyncio
    async def test_notify_spectator_on_consensus(self):
        """Should notify spectator of consensus result."""
        protocol = MockProtocol(consensus="majority")
        notify = MagicMock()

        async def vote_with_agent(agent, proposals, task):
            return MockVote(agent=agent.name, choice="claude", confidence=0.8)

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=vote_with_agent,
            notify_spectator=notify,
            group_similar_votes=lambda votes: {"claude": ["claude"]},
        )

        agents = [MockAgent(name="claude")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        # Check consensus notification
        consensus_calls = [c for c in notify.call_args_list if c[0][0] == "consensus"]
        assert len(consensus_calls) >= 1


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_empty_agents(self):
        """Should handle empty agents list."""
        protocol = MockProtocol(consensus="majority")

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=AsyncMock(),
            group_similar_votes=lambda votes: {},
        )

        ctx = DebateContext(env=MockEnvironment(), agents=[])
        ctx.proposals = {"claude": "Proposal A"}
        ctx.result = MockDebateResult()

        # Should not raise
        await phase.execute(ctx)

    @pytest.mark.asyncio
    async def test_empty_proposals(self):
        """Should handle empty proposals."""
        protocol = MockProtocol(consensus="none")

        phase = ConsensusPhase(protocol=protocol)

        ctx = DebateContext(env=MockEnvironment())
        ctx.proposals = {}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        assert ctx.result.final_answer == ""

    @pytest.mark.asyncio
    async def test_unknown_consensus_mode(self):
        """Should fall back to none mode for unknown consensus."""
        protocol = MockProtocol(consensus="unknown_mode")

        phase = ConsensusPhase(protocol=protocol)

        ctx = DebateContext(env=MockEnvironment())
        ctx.proposals = {"claude": "Proposal A"}
        ctx.result = MockDebateResult()

        await phase.execute(ctx)

        assert ctx.result.consensus_reached is False

    @pytest.mark.asyncio
    async def test_vote_error_handling(self):
        """Should continue on vote errors."""
        protocol = MockProtocol(consensus="majority")

        async def vote_with_agent(agent, proposals, task):
            if agent.name == "error_agent":
                raise Exception("Vote failed")
            return MockVote(agent=agent.name, choice="claude", confidence=0.8)

        phase = ConsensusPhase(
            protocol=protocol,
            vote_with_agent=vote_with_agent,
            group_similar_votes=lambda votes: {"claude": ["claude"]},
        )

        agents = [MockAgent(name="claude"), MockAgent(name="error_agent")]
        ctx = DebateContext(env=MockEnvironment(), agents=agents)
        ctx.proposals = {"claude": "Proposal A"}
        ctx.result = MockDebateResult()

        # Should not raise
        await phase.execute(ctx)

        # Should have one successful vote
        assert len(ctx.result.votes) == 1
