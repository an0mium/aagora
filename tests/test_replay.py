"""
Tests for debate replay functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from aragora.core import DebateResult, Environment, Message, Vote
from aragora.replay.replay import DebateRecorder, DebateReplayer


class TestDebateRecorder:
    """Test the DebateRecorder class."""

    def test_save_debate(self):
        """Test saving a debate result."""
        with tempfile.TemporaryDirectory() as temp_dir:
            recorder = DebateRecorder(temp_dir)

            # Create a mock debate result
            result = DebateResult(
                id="test-123",
                task="Test debate task",
                final_answer="Test answer",
                confidence=0.8,
                consensus_reached=True,
                messages=[
                    Message(role="proposer", agent="agent1", content="Proposal 1"),
                    Message(role="critic", agent="agent2", content="Critique of proposal 1"),
                ],
                votes=[Vote(agent="agent1", choice="accept", confidence=0.9, reasoning="Good proposal")],
                rounds_used=2,
                duration_seconds=10.5,
            )

            # Save the debate
            filepath = recorder.save_debate(result, {"test": "metadata"})

            # Verify file was created
            assert Path(filepath).exists()

            # Verify content
            with open(filepath, 'r') as f:
                data = json.load(f)

            assert data["debate_result"]["id"] == "test-123"
            assert data["debate_result"]["task"] == "Test debate task"
            assert data["metadata"]["test"] == "metadata"
            assert "recorded_at" in data

    def test_make_serializable(self):
        """Test converting objects to serializable format."""
        recorder = DebateRecorder()

        # Test with dict containing dataclass
        test_dict = {"result": DebateResult(id="test")}
        result = recorder._make_serializable(test_dict)

        assert isinstance(result, dict)
        assert result["result"]["id"] == "test"

        # Test with list
        test_list = [1, "string", {"key": "value"}]
        result = recorder._make_serializable(test_list)
        assert result == test_list


class TestDebateReplayer:
    """Test the DebateReplayer class."""

    def test_list_debates_empty(self):
        """Test listing debates when none exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            replayer = DebateReplayer(temp_dir)
            debates = replayer.list_debates()
            assert debates == []

    def test_list_debates_with_data(self):
        """Test listing debates with saved data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # First save a debate
            recorder = DebateRecorder(temp_dir)
            result = DebateResult(
                id="test-123",
                task="Test debate about AI safety",
                consensus_reached=True,
                confidence=0.9,
                duration_seconds=15.0,
                rounds_used=3,
            )
            recorder.save_debate(result)

            # Now list debates
            replayer = DebateReplayer(temp_dir)
            debates = replayer.list_debates()

            assert len(debates) == 1
            debate = debates[0]
            assert debate["task"] == "Test debate about AI safety"
            assert debate["consensus_reached"] is True
            assert debate["confidence"] == 0.9
            assert debate["duration_seconds"] == 15.0
            assert debate["rounds_used"] == 3

    def test_load_debate(self):
        """Test loading a specific debate."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save a debate
            recorder = DebateRecorder(temp_dir)
            original_result = DebateResult(
                id="test-456",
                task="Test loading functionality",
                final_answer="Loaded successfully",
            )
            filepath = recorder.save_debate(original_result)
            filename = Path(filepath).name

            # Load the debate
            replayer = DebateReplayer(temp_dir)
            loaded_result = replayer.load_debate(filename)

            assert loaded_result is not None
            assert loaded_result.id == "test-456"
            assert loaded_result.task == "Test loading functionality"
            assert loaded_result.final_answer == "Loaded successfully"

    def test_load_debate_not_found(self):
        """Test loading a non-existent debate."""
        with tempfile.TemporaryDirectory() as temp_dir:
            replayer = DebateReplayer(temp_dir)
            result = replayer.load_debate("nonexistent.json")
            assert result is None

    def test_replay_debate(self, capsys):
        """Test replaying a debate (captures output)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save a debate with messages
            recorder = DebateRecorder(temp_dir)
            result = DebateResult(
                id="replay-test",
                task="Test replay functionality",
                final_answer="Replay complete",
                messages=[
                    Message(role="proposer", agent="Agent1", content="First message"),
                    Message(role="critic", agent="Agent2", content="Second message"),
                ],
                consensus_reached=True,
                confidence=1.0,
                duration_seconds=5.0,
                rounds_used=1,
            )
            filepath = recorder.save_debate(result)
            filename = Path(filepath).name

            # Replay the debate
            replayer = DebateReplayer(temp_dir)
            replayed_result = replayer.replay_debate(filename, speed=10.0)  # Fast replay

            assert replayed_result is not None
            assert replayed_result.id == "replay-test"

            # Check output
            captured = capsys.readouterr()
            assert "REPLAYING DEBATE" in captured.out
            assert "Test replay functionality" in captured.out
            assert "[ 1] Agent1: First message" in captured.out
            assert "[ 2] Agent2: Second message" in captured.out
            assert "Final Answer: Replay complete" in captured.out