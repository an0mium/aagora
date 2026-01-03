"""
Audio mixing and concatenation for Aragora Broadcast.

Combines individual audio segments into a single podcast file.
"""

from pathlib import Path
from typing import List
import tempfile
import os

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


def mix_audio(audio_files: List[Path], output_path: Path, format: str = "mp3") -> bool:
    """
    Mix and concatenate audio files into a single output file.

    Args:
        audio_files: List of audio file paths to concatenate
        output_path: Path for the final mixed audio file
        format: Output format ('mp3', 'wav', etc.)

    Returns:
        True if successful, False otherwise
    """
    if not PYDUB_AVAILABLE:
        print("pydub not available. Install with: pip install pydub")
        return False

    if not audio_files:
        print("No audio files to mix")
        return False

    try:
        # Load and concatenate audio segments
        combined = AudioSegment.empty()

        for audio_file in audio_files:
            if not audio_file.exists():
                print(f"Audio file not found: {audio_file}")
                continue

            segment = AudioSegment.from_file(str(audio_file))
            combined += segment

        # Export the combined audio
        combined.export(str(output_path), format=format)
        return True

    except Exception as e:
        print(f"Error mixing audio: {e}")
        return False


def mix_audio_with_ffmpeg(audio_files: List[Path], output_path: Path) -> bool:
    """
    Fallback mixing using ffmpeg directly.

    Args:
        audio_files: List of audio file paths
        output_path: Output path

    Returns:
        True if successful
    """
    if not audio_files:
        return False

    try:
        # Create a temporary file list for ffmpeg
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for audio_file in audio_files:
                f.write(f"file '{audio_file.absolute()}'\n")
            file_list = f.name

        # Run ffmpeg concat
        import subprocess
        cmd = [
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", file_list, "-c", "copy", str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        os.unlink(file_list)  # Clean up

        return result.returncode == 0

    except Exception as e:
        print(f"FFmpeg mixing failed: {e}")
        return False