"""
Aragora Broadcast: Post-debate podcast engine.

Creates audio clips from debate traces for passive consumption and sharing.
"""

from .script_gen import generate_script, ScriptSegment
from .audio_engine import generate_audio, VOICE_MAP
from .mixer import mix_audio

__all__ = ["generate_script", "ScriptSegment", "generate_audio", "VOICE_MAP", "mix_audio"]