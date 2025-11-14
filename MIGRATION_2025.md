# Migration Guide - January 2025 Update

## Critical Changes

### ⚠️ Coqui TTS Removed (DISCONTINUED)

Coqui AI shut down and their TTS library is no longer maintained. We've migrated to **HuggingFace Transformers** with actively maintained models.

## What Changed

### Before (DEPRECATED ❌)
```python
# Old - used discontinued Coqui TTS
from TTS.api import TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
# Required voice files for cloning
```

### After (CURRENT ✅)
```python
# New - uses HuggingFace transformers
from transformers import pipeline
tts = pipeline("text-to-speech", model="suno/bark-small")
# No voice files needed!
```

## Updated Requirements

All packages updated to LATEST versions (Python 3.11/3.12 compatible):

| Package | Old Version | New Version | Change |
|---------|-------------|-------------|--------|
| fastapi | 0.109.0 | **0.115.5** | +6 versions |
| uvicorn | 0.27.0 | **0.32.1** | +5 versions |
| openai | 1.10.0 | **1.57.2** | +47 versions! |
| torch | 2.1.2 | **2.5.1** | Major update |
| pydantic | 2.5.3 | **2.10.3** | +5 versions |
| TTS | 0.22.0 | **REMOVED** | Discontinued |
| transformers | N/A | **4.47.1** | NEW |
| accelerate | N/A | **1.2.1** | NEW |

## TTS Models Available

### 1. Bark (suno/bark-small) - DEFAULT ✅
- **Fast** and multilingual
- **13 languages** supported
- Special tokens: `[laughs]`, `[sighs]`, `[music]`
- No voice files needed
- Works immediately after install

```python
# English
speech = tts("Hello, how are you?")

# With emotion
speech = tts("[clears throat] This is amazing [laughs]!")
```

### 2. Bark Full (suno/bark)
- Higher quality than bark-small
- Slower but better results
- Same features as bark-small

### 3. SpeechT5 (microsoft/speecht5_tts)
- High quality
- English only
- Requires speaker embeddings

### 4. Parler-TTS (parler-tts/parler-tts-mini-v1)
- Newest from HuggingFace
- Multilingual
- Controllable voice characteristics

## Migration Steps

### 1. Update Code

**Old main.py:**
```python
from TTS.api import TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
```

**New main.py:**
```python
from transformers import pipeline
tts = pipeline("text-to-speech", model="suno/bark-small")
```

### 2. Update Environment

**Old .env:**
```env
TTS_MODEL=tts_models/multilingual/multi-dataset/xtts_v2
DEFAULT_VOICE_PATH=voices/default_en.wav  # Required!
```

**New .env:**
```env
TTS_MODEL=suno/bark-small  # No voice file needed!
```

### 3. Update Dependencies

```bash
# Remove old environment
pip uninstall TTS -y

# Install new requirements
pip install -r requirements.txt
```

## Voice Cloning

### ❌ OLD: Coqui XTTS (REMOVED)
```python
# This NO LONGER WORKS
tts.clone_voice(text, speaker_wav="voice.wav")
```

### ✅ NEW: Use F5-TTS or StyleTTS2

Bark doesn't support voice cloning. If you need it:

**Option 1: F5-TTS** (Recommended)
```bash
pip install f5-tts
```
```python
from f5_tts import F5TTS
tts = F5TTS()
tts.infer(text, reference_audio="voice.wav")
```

**Option 2: StyleTTS2**
```bash
pip install styletts2
```
```python
from styletts2 import tts
result = tts.inference(text, reference="voice.wav")
```

## Supported Languages

### Bark:
`en`, `de`, `es`, `fr`, `hi`, `it`, `ja`, `ko`, `pl`, `pt`, `ru`, `tr`, `zh`

### SpeechT5:
`en` only

### Parler-TTS:
`en`, `es`, `fr`, `de`, `it`, `pt`, `pl`, `hi`

## Breaking Changes

1. ❌ **Voice files no longer needed** for default operation
2. ❌ **Voice cloning removed** (use F5-TTS or StyleTTS2 instead)
3. ❌ **Coqui-specific features removed** (emotion presets, etc.)
4. ✅ **New special tokens** for Bark: `[laughs]`, `[sighs]`, `[music]`

## Benefits

✅ **Actively maintained** - HuggingFace transformers is updated regularly
✅ **Python 3.11/3.12 support** - Works with latest Python
✅ **Simpler setup** - No voice files required
✅ **Latest features** - All packages at newest versions
✅ **Better integration** - Part of HuggingFace ecosystem
✅ **Immediate use** - Works out of the box

## Testing

After migration, test with:

```python
from transformers import pipeline

tts = pipeline("text-to-speech", model="suno/bark-small")
speech = tts("Hello, this is a test!")

# Save to file
import scipy.io.wavfile
scipy.io.wavfile.write("test.wav", rate=speech["sampling_rate"], data=speech["audio"])
```

## Troubleshooting

### "No module named 'TTS'"
✅ This is expected - Coqui TTS was removed
✅ Use transformers instead

### "Voice cloning doesn't work"
✅ Bark doesn't support voice cloning
✅ Use F5-TTS or StyleTTS2 for voice cloning

### "Model too slow"
✅ Use `suno/bark-small` instead of `suno/bark`
✅ Enable GPU: `pip install torch --index-url https://download.pytorch.org/whl/cu121`

### "Import errors after upgrade"
```bash
# Clean install
pip uninstall -y TTS coqui-tts
pip install --upgrade -r requirements.txt
```

## Support

- **HuggingFace Docs**: https://huggingface.co/docs/transformers/tasks/text-to-speech
- **Bark Model**: https://huggingface.co/suno/bark
- **F5-TTS** (for voice cloning): https://github.com/SWivid/F5-TTS
- **StyleTTS2** (for voice cloning): https://github.com/yl4579/StyleTTS2

## Summary

| Feature | Old (Coqui) | New (HuggingFace) |
|---------|-------------|-------------------|
| Maintenance | ❌ Discontinued | ✅ Active |
| Python Support | 3.9-3.10 | ✅ 3.9-3.12 |
| Voice Files | Required | ✅ Not needed |
| Voice Cloning | Built-in | Use F5-TTS |
| Languages | 17 | 13 (Bark) |
| Setup | Complex | ✅ Simple |
| Updates | None | ✅ Regular |

**Bottom line**: Modern, maintained, easier to use!
