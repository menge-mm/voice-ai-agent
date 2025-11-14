"""
Text-to-Speech Engine using HuggingFace Transformers
Using MAINTAINED models: Bark, SpeechT5, Parler-TTS (2025)
"""

import torch
from transformers import pipeline
import io
import scipy.io.wavfile
from pathlib import Path
import logging
from typing import Optional, Generator
import os

logger = logging.getLogger(__name__)


class TransformersTTSEngine:
    """
    Text-to-Speech engine using HuggingFace Transformers
    Supports multiple models: Bark (default), Speech T5, Parler-TTS
    """

    def __init__(
        self,
        model_name: str = "suno/bark-small",
        force_cpu: bool = False
    ):
        """
        Initialize TTS engine

        Supported models:
        - "suno/bark-small" - Fast, multilingual, expressive (DEFAULT)
        - "suno/bark" - Full Bark model, higher quality
        - "microsoft/speecht5_tts" - High quality, requires speaker embeddings
        - "parler-tts/parler-tts-mini-v1" - Latest from HuggingFace
        """
        self.model_name = model_name
        self.tts_pipeline = None
        self.device = "cpu" if force_cpu else ("cuda" if torch.cuda.is_available() else "cpu")
        self.is_loaded = False
        self.supported_languages = self._get_supported_languages()

    def _get_supported_languages(self) -> list:
        """Get supported languages based on model"""
        if "bark" in self.model_name.lower():
            # Bark supports multiple languages
            return ["en", "de", "es", "fr", "hi", "it", "ja", "ko", "pl", "pt", "ru", "tr", "zh"]
        elif "speecht5" in self.model_name.lower():
            # SpeechT5 primarily English
            return ["en"]
        elif "parler" in self.model_name.lower():
            # Parler-TTS is multilingual
            return ["en", "es", "fr", "de", "it", "pt", "pl", "hi"]
        else:
            return ["en"]

    def load_model(self):
        """Load the TTS model into memory"""
        if self.is_loaded:
            logger.info("TTS model already loaded")
            return

        try:
            logger.info(f"Loading TTS model '{self.model_name}' on {self.device}...")

            # Initialize TTS pipeline
            self.tts_pipeline = pipeline(
                "text-to-speech",
                model=self.model_name,
                device=0 if self.device == "cuda" else -1
            )

            self.is_loaded = True
            logger.info(f"✓ TTS model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"✗ Failed to load TTS model: {e}")
            raise

    def synthesize(
        self,
        text: str,
        language: str = "en",
        speaker_wav: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs
    ) -> bytes:
        """
        Synthesize speech from text

        Args:
            text: Text to convert to speech
            language: Language code (currently used for validation only)
            speaker_wav: Not used for Bark (kept for API compatibility)
            output_path: Optional path to save audio file
            **kwargs: Additional parameters for the model

        Returns:
            Audio data as bytes (WAV format)
        """
        if not self.is_loaded:
            self.load_model()

        # Validate language
        if language not in self.supported_languages:
            logger.warning(f"Language '{language}' may not be supported, using default")

        try:
            logger.info(f"Synthesizing text: {text[:50]}...")

            # Generate speech using transformers pipeline
            # Bark supports special tokens like [laughs], [sighs], etc.
            forward_params = kwargs.get("forward_params", {"do_sample": True})

            speech = self.tts_pipeline(
                text,
                forward_params=forward_params
            )

            # Extract audio data and sampling rate
            audio_array = speech["audio"]
            sampling_rate = speech["sampling_rate"]

            # Convert to WAV bytes
            audio_buffer = io.BytesIO()

            # Ensure audio is in correct format
            if isinstance(audio_array, torch.Tensor):
                audio_array = audio_array.cpu().numpy()

            # Flatten if multi-dimensional
            if len(audio_array.shape) > 1:
                audio_array = audio_array.squeeze()

            # Write as WAV using scipy
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
            raise

    def synthesize_streaming(
        self,
        text: str,
        language: str = "en",
        speaker_wav: Optional[str] = None,
        chunk_size: int = 4096
    ) -> Generator[bytes, None, None]:
        """
        Synthesize speech and yield chunks for streaming

        Args:
            text: Text to convert to speech
            language: Language code
            speaker_wav: Not used for Bark
            chunk_size: Size of chunks to yield

        Yields:
            Audio data chunks
        """
        # Generate full audio
        audio_bytes = self.synthesize(text, language, speaker_wav)

        # Yield in chunks
        for i in range(0, len(audio_bytes), chunk_size):
            yield audio_bytes[i:i + chunk_size]

    def clone_voice(
        self,
        text: str,
        speaker_wav_path: str,
        language: str = "en"
    ) -> bytes:
        """
        Voice cloning not directly supported by Bark
        Returns standard synthesis

        For true voice cloning, use:
        - StyleTTS2
        - F5-TTS
        - Tortoise TTS

        Args:
            text: Text to speak
            speaker_wav_path: Path to reference audio (not used for Bark)
            language: Language to speak in

        Returns:
            Audio bytes with standard voice
        """
        logger.warning(
            "Voice cloning not supported with Bark. "
            "For voice cloning, consider using F5-TTS or StyleTTS2. "
            "Generating with default voice."
        )

        return self.synthesize(
            text=text,
            language=language
        )

    def set_default_voice(self, voice_path: str):
        """
        Set default voice - not applicable for Bark
        Kept for API compatibility
        """
        logger.warning("Default voice setting not applicable for Bark model")

    def get_supported_languages(self) -> list:
        """Return list of supported languages"""
        return self.supported_languages

    def is_ready(self) -> bool:
        """Check if TTS engine is loaded and ready"""
        return self.is_loaded

    def unload_model(self):
        """Unload the model from memory"""
        if self.is_loaded:
            del self.tts_pipeline
            self.tts_pipeline = None
            self.is_loaded = False
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("✓ TTS model unloaded")


# Backwards compatibility alias
XTTSEngine = TransformersTTSEngine
