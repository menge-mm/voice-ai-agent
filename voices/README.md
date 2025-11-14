# Voice Files Directory

This directory stores voice samples for TTS (Text-to-Speech) voice cloning.

## Requirements

- **Format**: WAV, MP3, OGG, FLAC, or M4A
- **Duration**: Minimum 6 seconds of clear speech
- **Quality**: Clear audio, minimal background noise
- **Content**: Natural speech, preferably in target language

## Directory Structure

```
voices/
├── en_default.wav       # Default English voice
├── es_default.wav       # Default Spanish voice
├── fr_default.wav       # Default French voice
├── custom/              # Custom user voices
│   ├── user1.wav
│   └── user2.wav
└── README.md           # This file
```

## Adding Voice Files

### Option 1: Record Your Own
```bash
# Use any audio recording software to record 6+ seconds of clear speech
# Save as WAV format for best quality
# Place in this directory
```

### Option 2: Use Sample Voices

Download free voice samples from:
- **Mozilla Common Voice**: https://commonvoice.mozilla.org/
- **LibriVox**: https://librivox.org/
- **OpenSLR**: https://www.openslr.org/

### Option 3: Generate with TTS

You can use other TTS systems to generate initial voices, then clone and customize them.

## Usage

### Set Default Voice

In your `.env` file:
```env
DEFAULT_VOICE_PATH=voices/en_default.wav
```

### Clone Voice via API

```bash
curl -X POST "http://localhost:8000/api/tts/clone-voice" \
  -F "text=Hello from my cloned voice!" \
  -F "language=en" \
  -F "voice_file=@voices/custom/myvoice.wav" \
  --output cloned_speech.wav
```

## Tips for Best Results

1. **Clear Speech**: Record in a quiet environment
2. **Natural Tone**: Speak naturally, not monotone
3. **Proper Length**: 6-15 seconds is ideal (longer is better)
4. **Target Language**: Use speech in the language you want to generate
5. **Audio Quality**: Use a good microphone if possible

## Example Voice Files

You can find example voice files in the project repository or download from the sources mentioned above.

## Note

Voice files are gitignored by default. Add `!voices/*.wav` to `.gitignore` if you want to commit specific voice files.
