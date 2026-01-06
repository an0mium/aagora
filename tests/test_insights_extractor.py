"""
Tests for aragora.insights.extractor module.

Tests InsightExtractor and supporting dataclasses.
"""

import pytest
from dataclasses import dataclass, field
from unittest.mock import MagicMock

from aragora.insights.extractor import (
    InsightType,
    Insight,
    AgentPerformance,
    DebateInsights,
    InsightExtractor,
)


# ============================================================================
# Test Data Fixtures
# ============================================================================

@dataclass
class MockCritique:
    """Mock critique object."""
    agent: str = "claude"
    target_agent: str = "gpt4"
    issues: list = field(default_factory=list)
    severity: float = 0.5


@dataclass
class MockVote:
    """Mock vote object."""
    agent: str = "claude"
    choice: str = "A"


@dataclass
class MockMessage:
    """Mock message object."""
    agent: str = "claude"
    content: str = "Test message"


@dataclass
class MockDebateResult:
    """Mock debate result for testing."""
    id: str = "debate_001"
    task: str = "Test task"
    consensus_reached: bool = True
    confidence: float = 0.85
    duration_seconds: float = 120.0
    final_answer: str = "The answer is X"
    consensus_strength: str = "strong"
    rounds_used: int = 3
    consensus_variance: float = 0.1
    messages: list = field(default_factory=list)
    critiques: list = field(default_factory=list)
    votes: list = field(default_factory=list)
    dissenting_views: list = field(default_factory=list)


# ============================================================================
# Insight Dataclass Tests
# ============================================================================

class TestInsight:
    """Tests for Insight dataclass."""

    def test_to_dict_all_fields(self):
        """Should serialize all fields."""
        insight = Insight(
            id="test_insight",
            type=InsightType.CONSENSUS,
            title="Test Title",
            description="Test description",
            confidence=0.9,
            debate_id="debate_001",
            agents_involved=["claude", "gpt4"],
            evidence=["evidence1"],
            metadata={"key": "value"},
        )
        d = insight.to_dict()

        assert d["id"] == "test_insight"
        assert d["type"] == "consensus"
        assert d["title"] == "Test Title"
        assert d["confidence"] == 0.9
        assert d["debate_id"] == "debate_001"
        assert d["agents_involved"] == ["claude", "gpt4"]
        assert d["metadata"]["key"] == "value"

    def test_insight_types(self):
        """Should have expected insight types."""
        assert InsightType.CONSENSUS.value == "consensus"
        assert InsightType.DISSENT.value == "dissent"
        assert InsightType.PATTERN.value == "pattern"
        assert InsightType.CONVERGENCE.value == "convergence"
        assert InsightType.AGENT_PERFORMANCE.value == "agent_perf"
        assert InsightType.FAILURE_MODE.value == "failure_mode"
        assert InsightType.DECISION_PROCESS.value == "decision"


class TestAgentPerformance:
    """Tests for AgentPerformance dataclass."""

    def test_default_values(self):
        """Should have sensible defaults."""
        perf = AgentPerformance(agent_name="claude")

        assert perf.agent_name == "claude"
        assert perf.proposals_made == 0
        assert perf.critiques_given == 0
        assert perf.contribution_score == 0.5

    def test_all_fields(self):
        """Should store all performance metrics."""
        perf = AgentPerformance(
            agent_name="gpt4",
            proposals_made=5,
            critiques_given=3,
            critiques_received=2,
            proposal_accepted=True,
            vote_aligned_with_consensus=True,
            average_critique_severity=0.3,
            contribution_score=0.8,
        )

        assert perf.proposals_made == 5
        assert perf.critiques_given == 3
        assert perf.proposal_accepted is True
        assert perf.contribution_score == 0.8


class TestDebateInsights:
    """Tests for DebateInsights dataclass."""

    def test_all_insights_empty(self):
        """Should return empty list when no insights."""
        insights = DebateInsights(
            debate_id="d001",
            task="Test",
            consensus_reached=True,
            duration_seconds=60.0,
        )

        assert insights.all_insights() == []

    def test_all_insights_with_content(self):
        """Should collect all insights types."""
        consensus = Insight(
            id="c1", type=InsightType.CONSENSUS, title="T",
            description="D", confidence=0.9, debate_id="d001",
        )
        dissent = Insight(
            id="d1", type=InsightType.DISSENT, title="T",
            description="D", confidence=0.6, debate_id="d001",
        )
        pattern = Insight(
            id="p1", type=InsightType.PATTERN, title="T",
            description="D", confidence=0.7, debate_id="d001",
        )

        insights = DebateInsights(
            debate_id="d001",
            task="Test",
            consensus_reached=True,
            duration_seconds=60.0,
            consensus_insight=consensus,
            dissent_insights=[dissent],
            pattern_insights=[pattern],
        )

        all_insights = insights.all_insights()
        assert len(all_insights) == 3
        assert consensus in all_insights
        assert dissent in all_insights
        assert pattern in all_insights


# ============================================================================
# InsightExtractor Tests
# ============================================================================

class TestInsightExtractor:
    """Tests for InsightExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create an InsightExtractor instance."""
        return InsightExtractor()

    @pytest.mark.asyncio
    async def test_extract_basic(self, extractor):
        """Should extract basic insights from result."""
        result = MockDebateResult(
            messages=[MockMessage(agent="claude")],
        )

        insights = await extractor.extract(result)

        assert insights.debate_id == "debate_001"
        assert insights.task == "Test task"
        assert insights.consensus_reached is True

    @pytest.mark.asyncio
    async def test_extract_consensus_insight(self, extractor):
        """Should extract consensus insight when consensus reached."""
        result = MockDebateResult(
            consensus_reached=True,
            final_answer="The solution is X",
            consensus_strength="unanimous",
        )

        insights = await extractor.extract(result)

        assert insights.consensus_insight is not None
        assert insights.consensus_insight.type == InsightType.CONSENSUS
        assert "unanimous" in insights.consensus_insight.title.lower()

    @pytest.mark.asyncio
    async def test_extract_no_consensus_insight_when_not_reached(self, extractor):
        """Should not extract consensus insight when no consensus."""
        result = MockDebateResult(consensus_reached=False)

        insights = await extractor.extract(result)

        assert insights.consensus_insight is None

    @pytest.mark.asyncio
    async def test_extract_dissent_insights(self, extractor):
        """Should extract dissent insights."""
        result = MockDebateResult(
            dissenting_views=[
                "[claude]: I disagree because X",
                "[gpt4]: Alternative approach is Y",
            ],
        )

        insights = await extractor.extract(result)

        assert len(insights.dissent_insights) == 2
        assert all(i.type == InsightType.DISSENT for i in insights.dissent_insights)

    @pytest.mark.asyncio
    async def test_extract_failure_mode_when_no_consensus(self, extractor):
        """Should extract failure mode when consensus not reached."""
        result = MockDebateResult(
            consensus_reached=False,
            votes=[MockVote(agent="a", choice="X"), MockVote(agent="b", choice="Y")],
        )

        insights = await extractor.extract(result)

        assert insights.failure_mode_insight is not None
        assert insights.failure_mode_insight.type == InsightType.FAILURE_MODE

    @pytest.mark.asyncio
    async def test_extract_pattern_insights(self, extractor):
        """Should extract pattern insights from critiques."""
        result = MockDebateResult(
            critiques=[
                MockCritique(agent="a", issues=["security vulnerability found"]),
                MockCritique(agent="b", issues=["authentication issue"]),
                MockCritique(agent="c", issues=["performance problem"]),
            ],
        )

        insights = await extractor.extract(result)

        # Should find security pattern (2 mentions)
        security_patterns = [
            p for p in insights.pattern_insights
            if "security" in p.title.lower()
        ]
        assert len(security_patterns) == 1

    @pytest.mark.asyncio
    async def test_extract_convergence_insight(self, extractor):
        """Should extract convergence insight from messages."""
        # Create messages with decreasing length (convergence)
        result = MockDebateResult(
            messages=[
                MockMessage(content="A" * 100),
                MockMessage(content="B" * 100),
                MockMessage(content="C" * 50),
                MockMessage(content="D" * 50),
            ],
        )

        insights = await extractor.extract(result)

        assert insights.convergence_insight is not None
        assert insights.convergence_insight.type == InsightType.CONVERGENCE

    @pytest.mark.asyncio
    async def test_extract_decision_insight(self, extractor):
        """Should extract decision process insight."""
        result = MockDebateResult(
            votes=[
                MockVote(agent="a", choice="X"),
                MockVote(agent="b", choice="X"),
            ],
            rounds_used=3,
        )

        insights = await extractor.extract(result)

        assert insights.decision_insight is not None
        assert insights.decision_insight.type == InsightType.DECISION_PROCESS

    @pytest.mark.asyncio
    async def test_extract_agent_performances(self, extractor):
        """Should extract agent performance metrics."""
        result = MockDebateResult(
            messages=[
                {"agent": "claude", "content": "X"},
                {"agent": "claude", "content": "Y"},
                {"agent": "gpt4", "content": "Z"},
            ],
            critiques=[
                MockCritique(agent="gpt4", target_agent="claude", severity=0.3),
            ],
        )

        insights = await extractor.extract(result)

        assert len(insights.agent_performances) >= 2

        claude_perf = next(
            (p for p in insights.agent_performances if p.agent_name == "claude"),
            None,
        )
        assert claude_perf is not None
        assert claude_perf.proposals_made == 2

    @pytest.mark.asyncio
    async def test_key_takeaway_consensus(self, extractor):
        """Should generate key takeaway for consensus."""
        result = MockDebateResult(
            consensus_reached=True,
            consensus_strength="strong",
            duration_seconds=90.0,
        )

        insights = await extractor.extract(result)

        assert "consensus" in insights.key_takeaway.lower()

    @pytest.mark.asyncio
    async def test_key_takeaway_no_consensus(self, extractor):
        """Should generate key takeaway for no consensus."""
        result = MockDebateResult(
            consensus_reached=False,
        )

        insights = await extractor.extract(result)

        assert "consensus" in insights.key_takeaway.lower()


class TestInsightExtractorHelpers:
    """Tests for InsightExtractor helper methods."""

    @pytest.fixture
    def extractor(self):
        return InsightExtractor()

    def test_categorize_issue_security(self, extractor):
        """Should categorize security issues."""
        assert extractor._categorize_issue("SQL injection risk") == "security"
        assert extractor._categorize_issue("authentication bypass") == "security"

    def test_categorize_issue_performance(self, extractor):
        """Should categorize performance issues."""
        assert extractor._categorize_issue("slow response time") == "performance"
        assert extractor._categorize_issue("optimize query") == "performance"

    def test_categorize_issue_correctness(self, extractor):
        """Should categorize correctness issues."""
        assert extractor._categorize_issue("bug in calculation") == "correctness"
        assert extractor._categorize_issue("error handling missing") == "correctness"

    def test_categorize_issue_unknown(self, extractor):
        """Should return None for uncategorized issues."""
        assert extractor._categorize_issue("some random issue") is None

    def test_get_agent_names_from_messages(self, extractor):
        """Should extract agent names from messages."""
        result = MockDebateResult(
            messages=[
                {"agent": "claude", "content": "x"},
                {"agent": "gpt4", "content": "y"},
                {"agent": "claude", "content": "z"},
            ],
        )

        names = extractor._get_agent_names(result)

        assert set(names) == {"claude", "gpt4"}

    def test_get_agent_names_from_critiques(self, extractor):
        """Should extract agent names from critiques."""
        result = MockDebateResult(
            critiques=[MockCritique(agent="gemini")],
        )

        names = extractor._get_agent_names(result)

        assert "gemini" in names

    def test_get_agent_names_from_votes(self, extractor):
        """Should extract agent names from votes."""
        result = MockDebateResult(
            votes=[MockVote(agent="mistral")],
        )

        names = extractor._get_agent_names(result)

        assert "mistral" in names


class TestInsightExtractorEdgeCases:
    """Edge case tests for InsightExtractor."""

    @pytest.fixture
    def extractor(self):
        return InsightExtractor()

    @pytest.mark.asyncio
    async def test_extract_with_empty_result(self, extractor):
        """Should handle empty result gracefully."""
        result = MockDebateResult(
            id="empty",
            task="",
            messages=[],
            critiques=[],
            votes=[],
        )

        insights = await extractor.extract(result)

        assert insights.debate_id == "empty"
        assert insights.total_insights >= 0

    @pytest.mark.asyncio
    async def test_extract_with_long_task(self, extractor):
        """Should truncate long tasks."""
        result = MockDebateResult(
            task="A" * 500,
        )

        insights = await extractor.extract(result)

        assert len(insights.task) == 200

    @pytest.mark.asyncio
    async def test_extract_with_dict_messages(self, extractor):
        """Should handle dict-style messages."""
        result = MockDebateResult()
        result.messages = [{"agent": "claude", "content": "test"}]

        insights = await extractor.extract(result)

        # Should not crash
        assert insights.debate_id is not None

    @pytest.mark.asyncio
    async def test_extract_generates_id_from_hash(self, extractor):
        """Should generate ID when not provided."""
        @dataclass
        class ResultWithoutId:
            task: str = "Test"
            consensus_reached: bool = False
            duration_seconds: float = 10.0

        result = ResultWithoutId()
        insights = await extractor.extract(result)

        assert insights.debate_id is not None
        assert len(insights.debate_id) == 16
