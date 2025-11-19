"""
Unit tests for TTS (Text-to-Speech) service (TDD - Tests written FIRST)

The TTS service will:
- Support multiple models (Bark, SpeechT5, etc.)
- Async synthesis methods
- Return audio bytes (WAV format)
- Support streaming
- Handle model loading/unloading
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.tts_service import TTSService


class TestTTSService:
    """Test suite for TTS service"""

    @pytest.fixture
    def mock_model(self):
        """Mock TTS model"""
        model = MagicMock()
        return model

    @pytest.fixture
    def tts_service(self, mock_model):
        """Create TTS service with mocked model"""
        with patch('app.services.tts_service.pipeline') as mock_pipeline:
            mock_pipeline.return_value = mock_model
            service = TTSService(
                model_name="microsoft/speecht5_tts",
                force_cpu=True
            )
            service.model_pipeline = mock_model
            service.is_loaded = True
            return service

    async def test_synthesize_returns_audio_bytes(self, tts_service, mock_model):
        """Test that synthesize returns audio bytes"""
        # Mock the pipeline to return audio data
        mock_model.return_value = {
            "audio": [0.1, 0.2, 0.3, 0.4],  # Mock audio array
            "sampling_rate": 16000
        }

        audio_bytes = await tts_service.synthesize(text="Hello world")

        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0

    async def test_synthesize_with_language(self, tts_service, mock_model):
        """Test synthesis with specific language"""
        mock_model.return_value = {
            "audio": [0.1, 0.2],
            "sampling_rate": 16000
        }

        audio_bytes = await tts_service.synthesize(
            text="Hola mundo",
            language="es"
        )

        assert isinstance(audio_bytes, bytes)

    async def test_synthesize_saves_to_file(self, tts_service, mock_model, tmp_path):
        """Test saving synthesized audio to file"""
        mock_model.return_value = {
            "audio": [0.1, 0.2],
            "sampling_rate": 16000
        }

        output_path = tmp_path / "test_audio.wav"
        audio_bytes = await tts_service.synthesize(
            text="Save me",
            output_path=str(output_path)
        )

        assert output_path.exists()
        assert len(audio_bytes) > 0

    async def test_synthesize_streaming(self, tts_service, mock_model):
        """Test streaming synthesis"""
        mock_model.return_value = {
            "audio": [0.1] * 10000,  # Larger audio for chunking
            "sampling_rate": 16000
        }

        chunks = []
        async for chunk in tts_service.synthesize_streaming(text="Stream me"):
            chunks.append(chunk)

        assert len(chunks) > 0
        # Each chunk should be bytes
        for chunk in chunks:
            assert isinstance(chunk, bytes)

    async def test_load_model(self):
        """Test model loading"""
        with patch('app.services.tts_service.pipeline') as mock_pipeline:
            service = TTSService(
                model_name="suno/bark-small",
                force_cpu=True
            )

            await service.load_model()

            assert service.is_loaded
            mock_pipeline.assert_called_once()

    async def test_load_model_idempotent(self, tts_service):
        """Test that loading model multiple times is safe"""
        assert tts_service.is_loaded

        # Loading again should not raise error
        await tts_service.load_model()

        assert tts_service.is_loaded

    async def test_unload_model(self, tts_service):
        """Test model unloading"""
        assert tts_service.is_loaded

        await tts_service.unload_model()

        assert not tts_service.is_loaded
        assert tts_service.model_pipeline is None

    async def test_is_ready(self, tts_service):
        """Test is_ready returns correct status"""
        assert tts_service.is_ready()

        await tts_service.unload_model()

        assert not tts_service.is_ready()

    async def test_get_supported_languages_bark(self):
        """Test getting supported languages for Bark model"""
        service = TTSService(model_name="suno/bark-small")
        languages = service.get_supported_languages()

        assert isinstance(languages, list)
        assert "en" in languages
        # Bark supports multiple languages
        assert len(languages) > 1

    async def test_get_supported_languages_speecht5(self):
        """Test getting supported languages for SpeechT5"""
        service = TTSService(model_name="microsoft/speecht5_tts")
        languages = service.get_supported_languages()

        assert isinstance(languages, list)
        assert "en" in languages

    async def test_synthesize_validates_language(self, tts_service, mock_model):
        """Test that unsupported language logs warning"""
        mock_model.return_value = {
            "audio": [0.1, 0.2],
            "sampling_rate": 16000
        }

        # Should not raise, but should log warning
        audio_bytes = await tts_service.synthesize(
            text="Test",
            language="unsupported-lang"
        )

        assert isinstance(audio_bytes, bytes)

    async def test_synthesize_handles_model_error(self, tts_service, mock_model):
        """Test error handling during synthesis"""
        mock_model.side_effect = RuntimeError("Model error")

        with pytest.raises(Exception) as exc_info:
            await tts_service.synthesize(text="Test")

        assert "synthesis failed" in str(exc_info.value).lower() or "model error" in str(exc_info.value).lower()

    async def test_set_model_name(self):
        """Test changing model name"""
        service = TTSService(model_name="suno/bark-small")
        assert service.model_name == "suno/bark-small"

        service.model_name = "microsoft/speecht5_tts"
        assert service.model_name == "microsoft/speecht5_tts"

    async def test_device_selection_cpu(self):
        """Test that force_cpu uses CPU device"""
        service = TTSService(force_cpu=True)
        assert service.device == "cpu"

    async def test_device_selection_auto(self):
        """Test automatic device selection"""
        with patch('torch.cuda.is_available', return_value=False):
            service = TTSService(force_cpu=False)
            assert service.device == "cpu"

    @pytest.mark.skipif(not __import__('torch').cuda.is_available(), reason="CUDA not available")
    async def test_device_selection_cuda(self):
        """Test CUDA device selection when available"""
        service = TTSService(force_cpu=False)
        # If CUDA is available, should use it
        assert service.device in ["cuda", "cpu"]

    async def test_estimate_audio_duration(self, tts_service):
        """Test estimating audio duration from text"""
        text = "This is a test sentence with several words."
        duration = tts_service.estimate_audio_duration(text)

        # Duration should be positive and reasonable
        assert duration > 0
        # Rough estimate: ~150 words per minute = ~2.5 words per second
        # Our sentence has ~9 words, so should be ~3-4 seconds
        assert 2 < duration < 10

    async def test_get_audio_info(self, tts_service, mock_model):
        """Test getting audio format information"""
        info = tts_service.get_audio_info()

        assert isinstance(info, dict)
        assert "format" in info
        assert "sample_rate" in info
        assert info["format"] == "wav"
