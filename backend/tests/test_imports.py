"""
Test that all required packages can be imported
Validates requirements.txt has all necessary dependencies
"""

import pytest


def test_import_fastapi():
    """Test FastAPI can be imported"""
    import fastapi
    assert fastapi.__version__ >= "0.115.0"


def test_import_uvicorn():
    """Test uvicorn can be imported"""
    import uvicorn
    assert uvicorn.__version__ >= "0.32.0"


def test_import_openai():
    """Test OpenAI can be imported"""
    import openai
    assert openai.__version__ >= "1.57.0"


def test_import_transformers():
    """Test transformers can be imported"""
    import transformers
    assert transformers.__version__ >= "4.47.0"


def test_import_torch():
    """Test PyTorch can be imported"""
    import torch
    assert torch.__version__ >= "2.5.0"


def test_import_pydantic():
    """Test Pydantic can be imported"""
    import pydantic
    assert pydantic.__version__ >= "2.10.0"


def test_import_scipy():
    """Test scipy can be imported"""
    import scipy
    assert scipy.__version__ >= "1.14.0"


def test_import_soundfile():
    """Test soundfile can be imported"""
    import soundfile
    # soundfile version should be available


def test_import_python_dotenv():
    """Test python-dotenv can be imported"""
    import dotenv
    # dotenv doesn't have __version__


def test_coqui_tts_not_installed():
    """Test that deprecated Coqui TTS is NOT installed"""
    with pytest.raises(ImportError):
        import TTS


def test_all_backend_modules():
    """Test all backend modules can be imported"""
    from backend import main
    from backend import tts_engine
    from backend import openai_integration


def test_tts_engine_class_exists():
    """Test TTS engine classes exist"""
    from backend.tts_engine import TransformersTTSEngine, XTTSEngine
    assert TransformersTTSEngine is not None
    assert XTTSEngine is TransformersTTSEngine  # Alias


def test_openai_client_class_exists():
    """Test OpenAI client class exists"""
    from backend.openai_integration import OpenAIClient
    assert OpenAIClient is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
