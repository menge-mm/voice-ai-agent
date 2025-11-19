"""
Text-to-Speech Service using HuggingFace Transformers

Production-ready TTS service with async methods, multiple model support,
and clean architecture.
"""

import torch
from transformers import pipeline
import io
import scipy.io.wavfile
import logging
from typing import Optional, AsyncGenerator, List, Dict
import numpy as np

logger = logging.getLogger(__name__)


class TTSService:
    """
    Text-to-Speech service using HuggingFace Transformers.

    Supports multiple models:
    - microsoft/speecht5_tts - Fast, lightweight, English only (~200MB)
    - suno/bark-small - Multilingual, expressive (2-3GB)
    - suno/bark - Full Bark model, higher quality

    Example:
        ```python
        tts = TTSService(model_name="microsoft/speecht5_tts")
        await tts.load_model()

        audio_bytes = await tts.synthesize("Hello world")
        ```
    """

    def __init__(
        self,
        model_name: str = "microsoft/speecht5_tts",
        force_cpu: bool = False
    ):
        """
        Initialize TTS service.

        Args:
            model_name: HuggingFace model name
            force_cpu: Force CPU usage even if CUDA available
        """
        self.model_name = model_name
        self.model_pipeline = None
        self.device = "cpu" if force_cpu else ("cuda" if torch.cuda.is_available() else "cpu")
        self.is_loaded = False
        self.supported_languages = self._get_supported_languages()

    def _get_supported_languages(self) -> List[str]:
        """Get supported languages based on model"""
        if "bark" in self.model_name.lower():
            return ["en", "de", "es", "fr", "hi", "it", "ja", "ko", "pl", "pt", "ru", "tr", "zh"]
        elif "speecht5" in self.model_name.lower():
            return ["en"]
        elif "parler" in self.model_name.lower():
            return ["en", "es", "fr", "de", "it", "pt", "pl", "hi"]
        else:
            return ["en"]

    async def load_model(self):
        """Load the TTS model into memory"""
        if self.is_loaded:
            logger.info("TTS model already loaded")
            return

        try:
            logger.info(f"Loading TTS model '{self.model_name}' on {self.device}...")

            # Use pipeline for all models (simplified from original)
            self.model_pipeline = pipeline(
                "text-to-speech",
                model=self.model_name,
                device=0 if self.device == "cuda" else -1
            )

            self.is_loaded = True
            logger.info(f"✓ TTS model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"✗ Failed to load TTS model: {e}")
            raise

    async def synthesize(
        self,
        text: str,
        language: str = "en",
        output_path: Optional[str] = None,
        **kwargs
    ) -> bytes:
        """
        Synthesize speech from text.

        Args:
            text: Text to convert to speech
            language: Language code
            output_path: Optional path to save audio file
            **kwargs: Additional parameters for the model

        Returns:
            Audio data as bytes (WAV format)
        """
        if not self.is_loaded:
            await self.load_model()

        # Validate language
        if language not in self.supported_languages:
            logger.warning(f"Language '{language}' may not be supported, using default")

        try:
            logger.info(f"Synthesizing text: {text[:50]}...")

            # Generate speech
            forward_params = kwargs.get("forward_params", {"do_sample": True})
            speech = self.model_pipeline(text, forward_params=forward_params)

            audio_array = speech["audio"]
            sampling_rate = speech["sampling_rate"]

            # Convert tensor to numpy if needed
            if isinstance(audio_array, torch.Tensor):
                audio_array = audio_array.cpu().numpy()

            # Ensure array is correct type
            if isinstance(audio_array, list):
                audio_array = np.array(audio_array, dtype=np.float32)

            # Flatten if multi-dimensional
            if len(audio_array.shape) > 1:
                audio_array = audio_array.squeeze()

            # Convert to WAV bytes
            audio_buffer = io.BytesIO()
            scipy.io.wavfile.write(
                audio_buffer,
                rate=sampling_rate,
                data=audio_array
            )

            audio_buffer.seek(0)
            audio_bytes = audio_buffer.read()

            # Save to file if requested
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(audio_bytes)
                logger.info(f"✓ Audio saved to {output_path}")

            logger.info(f"✓ Synthesized {len(audio_bytes)} bytes of audio")
            return audio_bytes

        except Exception as e:
            logger.error(f"✗ Synthesis failed: {e}")
            raise Exception(f"TTS synthesis failed: {e}")

    async def synthesize_streaming(
        self,
        text: str,
        language: str = "en",
        chunk_size: int = 4096
    ) -> AsyncGenerator[bytes, None]:
        """
        Synthesize speech and yield chunks for streaming.

        Args:
            text: Text to convert to speech
            language: Language code
            chunk_size: Size of chunks to yield

        Yields:
            Audio data chunks (bytes)
        """
        # Generate full audio first
        audio_bytes = await self.synthesize(text, language)

        # Yield in chunks
        for i in range(0, len(audio_bytes), chunk_size):
            yield audio_bytes[i:i + chunk_size]

    async def unload_model(self):
        """Unload the model from memory"""
        if self.is_loaded:
            del self.model_pipeline
            self.model_pipeline = None
            self.is_loaded = False

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("✓ TTS model unloaded")

    def is_ready(self) -> bool:
        """Check if TTS engine is loaded and ready"""
        return self.is_loaded

    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages"""
        return self.supported_languages

    def estimate_audio_duration(self, text: str) -> float:
        """
        Estimate audio duration in seconds.

        Uses rough approximation: ~150 words per minute

        Args:
            text: Text to estimate duration for

        Returns:
            Estimated duration in seconds
        """
        words = len(text.split())
        words_per_minute = 150
        duration_seconds = (words / words_per_minute) * 60
        return duration_seconds

    def get_audio_info(self) -> Dict[str, any]:
        """
        Get audio format information.

        Returns:
            Dictionary with format, sample_rate, etc.
        """
        return {
            "format": "wav",
            "sample_rate": 16000 if "speecht5" in self.model_name.lower() else 24000,
            "channels": 1,
            "bit_depth": 16
        }
