"""
Text-to-Speech Engine using HuggingFace Transformers
Using MAINTAINED models: Bark, SpeechT5, Parler-TTS (2025)
"""

import torch
from transformers import pipeline, SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
import io
import scipy.io.wavfile
from pathlib import Path
import logging
from typing import Optional, Generator
import os
import numpy as np

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
        - "microsoft/speecht5_tts" - Fast MVP, ~200MB, English only
        - "suno/bark-small" - Multilingual, expressive, 2-3GB
        - "suno/bark" - Full Bark model, higher quality
        - "parler-tts/parler-tts-mini-v1" - Latest from HuggingFace
        """
        self.model_name = model_name
        self.tts_pipeline = None
        self.model = None
        self.processor = None
        self.vocoder = None
        self.speaker_embeddings = None
        self.device = "cpu" if force_cpu else ("cuda" if torch.cuda.is_available() else "cpu")
        self.is_loaded = False
        self.supported_languages = self._get_supported_languages()
        self.is_speecht5 = "speecht5" in model_name.lower()

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

            if self.is_speecht5:
                # Load SpeechT5 components separately
                self.processor = SpeechT5Processor.from_pretrained(self.model_name)
                self.model = SpeechT5ForTextToSpeech.from_pretrained(self.model_name)
                self.vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")

                # Move to device
                self.model = self.model.to(self.device)
                self.vocoder = self.vocoder.to(self.device)

                # Load speaker embeddings - download from HuggingFace directly
                logger.info("Loading speaker embeddings from CMU Arctic...")

                from huggingface_hub import hf_hub_download
                import zipfile

                # Download the speaker embeddings zip file
                zip_path = hf_hub_download(
                    repo_id="Matthijs/cmu-arctic-xvectors",
                    filename="spkrec-xvect.zip",
                    repo_type="dataset"
                )

                # Extract and load speaker 7306 embedding
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # List all .npy files
                    npy_files = [f for f in zip_ref.namelist() if f.endswith('.npy')]
                    # Use file at index 7306 (good quality American male voice)
                    embedding_file = npy_files[7306] if len(npy_files) > 7306 else npy_files[0]

                    # Load the embedding
                    with zip_ref.open(embedding_file) as f:
                        embedding = np.load(f)
                        self.speaker_embeddings = torch.tensor(embedding).unsqueeze(0).to(self.device)

                logger.info(f"✓ Loaded CMU Arctic speaker embedding from {embedding_file}")
                logger.info("✓ SpeechT5 model loaded successfully")
            else:
                # Use pipeline for Bark and other models
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

            if self.is_speecht5:
                # SpeechT5 synthesis
                inputs = self.processor(text=text, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # Generate speech
                with torch.no_grad():
                    speech = self.model.generate_speech(
                        inputs["input_ids"],
                        self.speaker_embeddings,
                        vocoder=self.vocoder
                    )

                # Convert to numpy
                audio_array = speech.cpu().numpy()
                sampling_rate = 16000  # SpeechT5 uses 16kHz
            else:
                # Bark/other models synthesis
                forward_params = kwargs.get("forward_params", {"do_sample": True})
                speech = self.tts_pipeline(text, forward_params=forward_params)
                audio_array = speech["audio"]
                sampling_rate = speech["sampling_rate"]

                # Ensure audio is in correct format
                if isinstance(audio_array, torch.Tensor):
                    audio_array = audio_array.cpu().numpy()

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
