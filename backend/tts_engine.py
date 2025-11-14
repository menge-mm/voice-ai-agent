"""
Text-to-Speech Engine using Coqui XTTS-v2
Following implementation from huggingface.co/spaces/coqui/xtts
"""

import torch
from TTS.api import TTS
import io
import soundfile as sf
from pathlib import Path
import logging
from typing import Optional, Generator
import os

logger = logging.getLogger(__name__)


class XTTSEngine:
    """
    Text-to-Speech engine using Coqui XTTS-v2
    Supports 17 languages and voice cloning
    """

    def __init__(
        self,
        model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        force_cpu: bool = False
    ):
        self.model_name = model_name
        self.tts = None
        self.device = "cpu" if force_cpu else ("cuda" if torch.cuda.is_available() else "cpu")
        self.default_voice_path = None
        self.is_loaded = False
        self.supported_languages = [
            "en", "es", "fr", "de", "it", "pt", "pl", "tr",
            "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko", "hi"
        ]

    def load_model(self):
        """Load the XTTS model into memory"""
        if self.is_loaded:
            logger.info("TTS model already loaded")
            return

        try:
            logger.info(f"Loading XTTS model '{self.model_name}' on {self.device}...")

            # Initialize TTS with XTTS-v2
            self.tts = TTS(
                model_name=self.model_name,
                progress_bar=False,
                gpu=(self.device == "cuda")
            )

            # Move to device if CUDA
            if self.device == "cuda":
                self.tts.to(self.device)

            self.is_loaded = True
            logger.info(f"✓ XTTS model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"✗ Failed to load XTTS model: {e}")
            raise

    def synthesize(
        self,
        text: str,
        language: str = "en",
        speaker_wav: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Synthesize speech from text

        Args:
            text: Text to convert to speech
            language: Language code (en, es, fr, etc.)
            speaker_wav: Path to speaker reference audio for voice cloning
            output_path: Optional path to save audio file

        Returns:
            Audio data as bytes (WAV format)
        """
        if not self.is_loaded:
            self.load_model()

        # Validate language
        if language not in self.supported_languages:
            logger.warning(f"Language '{language}' not supported, falling back to 'en'")
            language = "en"

        # Use default voice if none provided
        if speaker_wav is None:
            speaker_wav = self.default_voice_path or self._get_default_voice(language)

        if not speaker_wav or not Path(speaker_wav).exists():
            raise ValueError(
                f"No voice file provided or found. "
                f"Please provide a speaker_wav or set DEFAULT_VOICE_PATH"
            )

        try:
            logger.info(f"Synthesizing text in '{language}': {text[:50]}...")

            # Generate speech using XTTS
            wav = self.tts.tts(
                text=text,
                speaker_wav=speaker_wav,
                language=language
            )

            # Convert to bytes (WAV format)
            audio_buffer = io.BytesIO()
            sf.write(
                audio_buffer,
                wav,
                samplerate=22050,  # XTTS output sample rate
                format='WAV'
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
            speaker_wav: Path to speaker reference audio
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
        Clone a voice from a reference audio and generate speech

        Args:
            text: Text to speak
            speaker_wav_path: Path to 6+ second audio of target voice
            language: Language to speak in

        Returns:
            Audio bytes with cloned voice
        """
        if not self.is_loaded:
            self.load_model()

        if not Path(speaker_wav_path).exists():
            raise FileNotFoundError(f"Voice file not found: {speaker_wav_path}")

        logger.info(f"Cloning voice from {speaker_wav_path}")

        return self.synthesize(
            text=text,
            language=language,
            speaker_wav=speaker_wav_path
        )

    def set_default_voice(self, voice_path: str):
        """Set the default voice for TTS"""
        voice_file = Path(voice_path)

        if not voice_file.exists():
            raise FileNotFoundError(f"Voice file not found: {voice_path}")

        self.default_voice_path = str(voice_file.absolute())
        logger.info(f"✓ Default voice set to {self.default_voice_path}")

    def get_supported_languages(self) -> list:
        """Return list of supported languages"""
        return self.supported_languages

    def _get_default_voice(self, language: str) -> Optional[str]:
        """
        Get default voice for a language from voices directory

        Args:
            language: Language code

        Returns:
            Path to default voice file or None
        """
        # Check environment variable
        env_voice = os.getenv("DEFAULT_VOICE_PATH")
        if env_voice and Path(env_voice).exists():
            return env_voice

        # Check in voices directory
        voices_dir = Path("voices")
        if voices_dir.exists():
            # Try language-specific voice
            voice_file = voices_dir / f"{language}_default.wav"
            if voice_file.exists():
                return str(voice_file.absolute())

            # Try generic default
            default_voice = voices_dir / "default.wav"
            if default_voice.exists():
                return str(default_voice.absolute())

        return None

    def is_ready(self) -> bool:
        """Check if TTS engine is loaded and ready"""
        return self.is_loaded

    def unload_model(self):
        """Unload the model from memory"""
        if self.is_loaded:
            del self.tts
            self.tts = None
            self.is_loaded = False
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("✓ TTS model unloaded")
