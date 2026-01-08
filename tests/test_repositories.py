"""
Tests for repository pattern implementations.

Tests MemoryRepository, DebateRepository, and EloRepository
using in-memory SQLite databases for isolation.
"""

import tempfile
from pathlib import Path

import pytest


class TestMemoryRepository:
    """Tests for MemoryRepository."""

    @pytest.fixture
    def repo(self):
        """Create a fresh MemoryRepository with temp database."""
        from aragora.persistence.repositories import MemoryRepository

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        repo = MemoryRepository(db_path)
        yield repo

        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    def test_add_memory_creates_entity(self, repo):
        """add_memory creates a new memory entity."""
        memory = repo.add_memory(
            agent_name="claude",
            content="Test observation",
            memory_type="observation",
            importance=0.7,
        )

        assert memory.id is not None
        assert memory.agent_name == "claude"
        assert memory.content == "Test observation"
        assert memory.memory_type == "observation"
        assert memory.importance == 0.7

    def test_add_memory_with_debate_id(self, repo):
        """add_memory can associate with a debate."""
        memory = repo.add_memory(
            agent_name="claude",
            content="Learned from debate",
            debate_id="debate-123",
        )

        assert memory.debate_id == "debate-123"

    def test_add_memory_with_metadata(self, repo):
        """add_memory stores metadata."""
        memory = repo.add_memory(
            agent_name="claude",
            content="Test with metadata",
            metadata={"source": "test", "round": 3},
        )

        assert memory.metadata["source"] == "test"
        assert memory.metadata["round"] == 3

    def test_observe_convenience_method(self, repo):
        """observe() creates observation type."""
        memory = repo.observe("claude", "Something happened")

        assert memory.memory_type == "observation"
        assert memory.importance == 0.5  # default

    def test_reflect_convenience_method(self, repo):
        """reflect() creates reflection type."""
        memory = repo.reflect("claude", "I learned something")

        assert memory.memory_type == "reflection"
        assert memory.importance == 0.7  # default for reflections

    def test_insight_convenience_method(self, repo):
        """insight() creates insight type."""
        memory = repo.insight("claude", "Key insight")

        assert memory.memory_type == "insight"
        assert memory.importance == 0.9  # default for insights

    def test_get_by_agent_returns_memories(self, repo):
        """get_by_agent retrieves all memories for agent."""
        repo.observe("claude", "Observation 1")
        repo.observe("claude", "Observation 2")
        repo.observe("other", "Other agent")

        memories = repo.get_by_agent("claude")

        assert len(memories) == 2
        assert all(m.agent_name == "claude" for m in memories)

    def test_get_by_agent_filters_by_type(self, repo):
        """get_by_agent can filter by memory type."""
        repo.observe("claude", "Observation")
        repo.reflect("claude", "Reflection")
        repo.insight("claude", "Insight")

        reflections = repo.get_by_agent("claude", memory_type="reflection")

        assert len(reflections) == 1
        assert reflections[0].memory_type == "reflection"

    def test_get_by_agent_filters_by_importance(self, repo):
        """get_by_agent respects min_importance threshold."""
        repo.add_memory("claude", "Low importance", importance=0.3)
        repo.add_memory("claude", "High importance", importance=0.8)

        memories = repo.get_by_agent("claude", min_importance=0.5)

        assert len(memories) == 1
        assert memories[0].importance == 0.8

    def test_get_by_agent_respects_limit(self, repo):
        """get_by_agent respects limit parameter."""
        for i in range(10):
            repo.observe("claude", f"Memory {i}")

        memories = repo.get_by_agent("claude", limit=5)

        assert len(memories) == 5

    def test_retrieve_ranks_by_score(self, repo):
        """retrieve returns memories ranked by combined score."""
        repo.add_memory("claude", "Low importance old", importance=0.3)
        repo.add_memory("claude", "High importance new", importance=0.9)

        retrieved = repo.retrieve("claude", limit=2)

        # Higher importance should rank first (recency similar)
        assert retrieved[0].memory.importance > retrieved[1].memory.importance

    def test_retrieve_with_query_uses_relevance(self, repo):
        """retrieve with query factors in relevance score."""
        repo.observe("claude", "Discussion about Python programming")
        repo.observe("claude", "Weather was nice today")

        retrieved = repo.retrieve("claude", query="Python programming")

        # Python-related should be first
        assert "Python" in retrieved[0].memory.content

    def test_should_reflect_false_initially(self, repo):
        """should_reflect returns False for new agents."""
        assert repo.should_reflect("new-agent") is False

    def test_should_reflect_after_threshold(self, repo):
        """should_reflect returns True after threshold memories."""
        for i in range(10):
            repo.observe("claude", f"Observation {i}")

        assert repo.should_reflect("claude", threshold=10) is True
        assert repo.should_reflect("claude", threshold=15) is False

    def test_mark_reflected_resets_counter(self, repo):
        """mark_reflected resets memories_since_reflection."""
        for i in range(15):
            repo.observe("claude", f"Observation {i}")

        assert repo.should_reflect("claude") is True

        repo.mark_reflected("claude")

        assert repo.should_reflect("claude") is False

    def test_get_reflection_schedule(self, repo):
        """get_reflection_schedule returns schedule state."""
        repo.observe("claude", "First observation")

        schedule = repo.get_reflection_schedule("claude")

        assert schedule is not None
        assert schedule.agent_name == "claude"
        assert schedule.memories_since_reflection == 1

    def test_get_stats_returns_counts(self, repo):
        """get_stats returns memory statistics."""
        repo.observe("claude", "Obs 1")
        repo.observe("claude", "Obs 2")
        repo.reflect("claude", "Reflect 1")
        repo.insight("claude", "Insight 1")

        stats = repo.get_stats("claude")

        assert stats["total_memories"] == 4
        assert stats["observations"] == 2
        assert stats["reflections"] == 1
        assert stats["insights"] == 1
        assert 0.5 <= stats["avg_importance"] <= 0.9

    def test_get_context_for_debate(self, repo):
        """get_context_for_debate returns formatted context."""
        repo.insight("claude", "Key insight about testing")
        repo.observe("claude", "Testing observation")

        context = repo.get_context_for_debate("claude", "testing strategies")

        assert "Relevant past experience" in context
        assert "[Insight]" in context or "[Experience]" in context

    def test_delete_by_agent_removes_memories(self, repo):
        """delete_by_agent removes all agent memories."""
        repo.observe("claude", "Memory 1")
        repo.observe("claude", "Memory 2")
        repo.observe("other", "Other memory")

        deleted = repo.delete_by_agent("claude")

        assert deleted == 2
        assert len(repo.get_by_agent("claude")) == 0
        assert len(repo.get_by_agent("other")) == 1

    def test_memory_entity_age_hours(self, repo):
        """MemoryEntity.age_hours calculates correctly."""
        memory = repo.observe("claude", "Recent memory")

        # Just created, should be near zero
        assert memory.age_hours < 0.01


class TestDebateRepository:
    """Tests for DebateRepository."""

    @pytest.fixture
    def repo(self):
        """Create a fresh DebateRepository with temp database."""
        from aragora.persistence.repositories import DebateRepository

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        repo = DebateRepository(db_path)
        yield repo

        Path(db_path).unlink(missing_ok=True)

    def test_save_and_get_debate(self, repo):
        """Can save and retrieve a debate."""
        from aragora.persistence.repositories import DebateEntity

        debate = DebateEntity(
            id="test-123",
            slug="test-debate",
            task="Test Task",
            agents=["claude", "gemini"],
            artifact_json="{}",
        )

        repo.save(debate)
        retrieved = repo.get("test-123")

        assert retrieved is not None
        assert retrieved.slug == "test-debate"
        assert retrieved.task == "Test Task"

    def test_get_by_slug(self, repo):
        """Can retrieve debate by slug."""
        from aragora.persistence.repositories import DebateRepository, DebateEntity

        debate = DebateEntity(
            id="test-456",
            slug="unique-slug",
            task="Unique Task",
            agents=["claude"],
            artifact_json="{}",
        )
        repo.save(debate)

        retrieved = repo.get_by_slug("unique-slug")

        assert retrieved is not None
        assert retrieved.id == "test-456"


class TestEloRepository:
    """Tests for EloRepository."""

    @pytest.fixture
    def repo(self):
        """Create a fresh EloRepository with temp database."""
        from aragora.persistence.repositories import EloRepository

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        repo = EloRepository(db_path)
        yield repo

        Path(db_path).unlink(missing_ok=True)

    def test_get_rating_creates_default_for_new_agent(self, repo):
        """get_rating creates default rating for unknown agent."""
        rating = repo.get_rating("new-agent")

        assert rating is not None
        assert rating.agent_name == "new-agent"
        assert rating.elo == 1500  # Default ELO

    def test_save_and_get_rating(self, repo):
        """Can save and retrieve a rating."""
        from aragora.persistence.repositories import RatingEntity

        rating = RatingEntity(
            agent_name="test-agent",
            elo=1200,
        )
        repo.save(rating)

        retrieved = repo.get_rating("test-agent")

        assert retrieved is not None
        assert retrieved.agent_name == "test-agent"
        assert retrieved.elo == 1200

    def test_record_match(self, repo):
        """Can record a match between agents."""
        from aragora.persistence.repositories import RatingEntity

        # Create ratings for both agents
        repo.save(RatingEntity(agent_name="agent1", elo=1000))
        repo.save(RatingEntity(agent_name="agent2", elo=1000))

        match_id = repo.record_match(
            debate_id="debate-1",
            winner="agent1",
            participants=["agent1", "agent2"],
            scores={"agent1": 1.0, "agent2": 0.0},
            elo_changes={"agent1": 16.0, "agent2": -16.0},
        )

        assert match_id is not None
        assert isinstance(match_id, int)

    def test_get_leaderboard(self, repo):
        """get_leaderboard returns ranked agents."""
        from aragora.persistence.repositories import RatingEntity

        repo.save(RatingEntity(agent_name="agent1", elo=1200))
        repo.save(RatingEntity(agent_name="agent2", elo=1100))

        leaderboard = repo.get_leaderboard(limit=10)

        assert len(leaderboard) >= 2
        # First should have higher rating
        assert leaderboard[0].elo >= leaderboard[1].elo
