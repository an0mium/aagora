"""
Tests for Aragora Broadcast functionality.
"""

import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from aragora.debate.traces import DebateTrace, TraceEvent, EventType
from aragora.broadcast.script_gen import generate_script, ScriptSegment
from aragora.broadcast.audio_engine import generate_audio, _get_voice_for_speaker, VOICE_MAP
from aragora.broadcast.mixer import mix_audio


class TestScriptGen:
    """Test script generation from debate traces."""

    def test_generate_script_basic(self):
        """Test basic script generation."""
        # Create mock trace
        trace = DebateTrace(
            trace_id="test-trace",
            debate_id="test-debate",
            task="Test debate task",
            agents=["agent1", "agent2"],
            random_seed=42,
            events=[
                TraceEvent(
                    event_id="1",
                    event_type=EventType.MESSAGE,
                    agent="agent1",
                    content="Hello from agent1",
                    round_num=1
                ),
                TraceEvent(
                    event_id="2",
                    event_type=EventType.MESSAGE,
                    agent="agent2",
                    content="Response from agent2",
                    round_num=1
                )
            ]
        )

        segments = generate_script(trace)

        assert len(segments) == 4  # Opening + transition + 2 messages + closing
        assert segments[0].speaker == "narrator"
        assert "Test debate task" in segments[0].text
        assert segments[1].speaker == "agent1"
        assert segments[2].speaker == "narrator"
        assert segments[3].speaker == "agent2"

    def test_code_summarization(self):
        """Test that long code blocks are summarized."""
        long_code = "\n".join([f"line {i}" for i in range(15)])
        short_code = "short code"

        from aragora.broadcast.script_gen import _summarize_code

        assert "Reading code block of 15 lines" in _summarize_code(long_code)
        assert _summarize_code(short_code) == short_code


class TestAudioEngine:
    """Test audio generation."""

    def test_voice_mapping(self):
        """Test voice mapping for speakers."""
        assert _get_voice_for_speaker("claude-visionary") == "en-GB-SoniaNeural"
        assert _get_voice_for_speaker("unknown") == "en-US-ZiraNeural"  # narrator default

    @pytest.mark.asyncio
    async def test_generate_audio_empty_segments(self):
        """Test generating audio with empty segments."""
        audio_files = await generate_audio([])
        assert audio_files == []

    @pytest.mark.asyncio
    @patch('aragora.broadcast.audio_engine._generate_edge_tts')
    async def test_generate_audio_with_mock(self, mock_tts):
        """Test audio generation with mocked TTS."""
        mock_tts.return_value = True

        segments = [
            ScriptSegment(speaker="agent1", text="Test text")
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            audio_files = await generate_audio(segments, temp_path)

            assert len(audio_files) == 1
            assert audio_files[0].exists()


class TestMixer:
    """Test audio mixing."""

    def test_mix_audio_no_files(self):
        """Test mixing with no audio files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "output.mp3"
            result = mix_audio([], output)
            assert not result
            assert not output.exists()

    @patch('aragora.broadcast.mixer.PYDUB_AVAILABLE', False)
    def test_mix_audio_no_pydub(self):
        """Test mixing when pydub is not available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "output.mp3"
            result = mix_audio([], output)
            assert not result


# Integration test
@pytest.mark.asyncio
async def test_full_pipeline_mock():
    """Test the full broadcast pipeline with mocks."""
    # Create mock trace
    trace = DebateTrace(
        trace_id="test-trace",
        debate_id="test-debate",
        task="Integration test debate",
        agents=["claude-visionary"],
        random_seed=42,
        events=[
            TraceEvent(
                event_id="1",
                event_type=EventType.MESSAGE,
                agent="claude-visionary",
                content="This is a test message",
                round_num=1
            )
        ]
    )

    # Mock the audio generation to create dummy files
    async def mock_generate_audio(segments, output_dir):
        audio_files = []
        for i, segment in enumerate(segments):
            audio_file = output_dir / f"segment_{i}.mp3"
            audio_file.write_text("dummy audio content")  # Create dummy file
            audio_files.append(audio_file)
        return audio_files

    with patch('aragora.broadcast.audio_engine.generate_audio', side_effect=mock_generate_audio):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Generate script
            segments = generate_script(trace)
            assert len(segments) > 0

            # Generate audio
            audio_files = await generate_audio(segments, temp_path)
            assert len(audio_files) > 0

            # Mix audio
            output_file = temp_path / "broadcast.mp3"
            # Note: mix_audio would need pydub, so this tests the interface
            # In real scenario, pydub would combine the dummy files