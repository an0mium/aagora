# Voice Reference Audio for XTTS

This directory contains voice reference audio files for Coqui XTTS v2 voice cloning.

## Setup

To enable voice cloning for debate broadcasts, add `.wav` files for each speaker:

```
voices/
├── claude.wav        # Claude-Visionary speaker
├── codex.wav         # Codex-Engineer speaker
├── gemini.wav        # Gemini-Visionary speaker
├── grok.wav          # Grok-Lateral-Thinker speaker
└── narrator.wav      # Narrator voice
```

## Requirements

- **Format**: WAV (16-bit PCM recommended)
- **Sample Rate**: 22050 Hz or 24000 Hz
- **Duration**: 6-15 seconds of clean speech
- **Quality**: Clear, no background noise or music

## Recording Tips

1. Record in a quiet environment
2. Use a decent microphone (even phone voice memos work)
3. Speak naturally with varied intonation
4. Avoid long pauses or filler words ("um", "uh")
5. Trim silence from start/end

## Example Script

Record each voice reading something like:

> "The quick brown fox jumps over the lazy dog.
> This is a sample of my voice for text-to-speech synthesis.
> I can speak at different speeds and with various emotions."

## Testing

After adding voice files:

```bash
# Test with ElevenLabs (cloud, fastest)
ARAGORA_TTS_BACKEND=elevenlabs python -c "
from aragora.broadcast.tts_backends import get_tts_backend
import asyncio

async def test():
    backend = get_tts_backend('elevenlabs')
    result = await backend.synthesize('Hello, this is a test.', voice='claude-visionary')
    print(f'Generated: {result}')

asyncio.run(test())
"

# Test with XTTS (local, uses reference audio)
ARAGORA_TTS_BACKEND=xtts python -c "
from aragora.broadcast.tts_backends import get_tts_backend
import asyncio

async def test():
    backend = get_tts_backend('xtts')
    result = await backend.synthesize('Hello, this is a test.', voice='claude-visionary')
    print(f'Generated: {result}')

asyncio.run(test())
"
```

## Notes

- If no reference audio exists, XTTS uses its default voice
- ElevenLabs doesn't use these files (it has its own voice library)
- Edge-TTS doesn't use these files (it uses Microsoft Azure voices)
