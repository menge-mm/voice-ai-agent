"""
Test TTS Engine functionality
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tts_engine import TransformersTTSEngine, XTTSEngine


def test_tts_engine_initialization():
    """Test TTS engine can be initialized"""
    engine = TransformersTTSEngine(force_cpu=True)
    assert engine is not None
    assert engine.model_name == "suno/bark-small"
    assert engine.device == "cpu"
    assert not engine.is_loaded


def test_tts_engine_custom_model():
    """Test TTS engine with custom model"""
    engine = TransformersTTSEngine(
        model_name="suno/bark",
        force_cpu=True
    )
    assert engine.model_name == "suno/bark"


def test_tts_supported_languages():
    """Test supported languages"""
    engine = TransformersTTSEngine(force_cpu=True)
    languages = engine.get_supported_languages()
    assert isinstance(languages, list)
    assert "en" in languages
    assert "es" in languages
    assert len(languages) >= 10  # Bark supports 13 languages


def test_tts_is_ready():
    """Test is_ready method"""
    engine = TransformersTTSEngine(force_cpu=True)
    assert not engine.is_ready()


def test_backwards_compatibility_alias():
    """Test XTTSEngine is alias for TransformersTTSEngine"""
    assert XTTSEngine is TransformersTTSEngine


def test_tts_engine_device_selection():
    """Test device selection logic"""
    import torch

    # Force CPU
    engine_cpu = TransformersTTSEngine(force_cpu=True)
    assert engine_cpu.device == "cpu"

    # Auto-detect (will be CPU in test environment)
    engine_auto = TransformersTTSEngine(force_cpu=False)
    if torch.cuda.is_available():
        assert engine_auto.device == "cuda"
    else:
        assert engine_auto.device == "cpu"


def test_tts_different_models_languages():
    """Test language support varies by model"""
    # Bark supports many languages
    bark_engine = TransformersTTSEngine(model_name="suno/bark-small", force_cpu=True)
    bark_langs = bark_engine.get_supported_languages()
    assert len(bark_langs) >= 10

    # SpeechT5 only English
    speecht5_engine = TransformersTTSEngine(model_name="microsoft/speecht5_tts", force_cpu=True)
    speecht5_langs = speecht5_engine.get_supported_languages()
    assert speecht5_langs == ["en"]


# Skip actual synthesis tests as they require model downloads
@pytest.mark.skip(reason="Requires model download")
def test_tts_load_model():
    """Test model loading (requires download)"""
    engine = TransformersTTSEngine(force_cpu=True)
    engine.load_model()
    assert engine.is_loaded


@pytest.mark.skip(reason="Requires model download")
def test_tts_synthesize():
    """Test speech synthesis (requires download)"""
    engine = TransformersTTSEngine(force_cpu=True)
    engine.load_model()

    audio_bytes = engine.synthesize("Hello, this is a test.")
    assert isinstance(audio_bytes, bytes)
    assert len(audio_bytes) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
