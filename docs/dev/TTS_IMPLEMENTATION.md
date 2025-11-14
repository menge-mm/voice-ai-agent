# Text-to-Speech (TTS) Implementation Guide

## Overview
This document details the implementation of Text-to-Speech functionality using Coqui XTTS-v2, following the approach used in popular HuggingFace Spaces.

## Why Coqui XTTS-v2?

Based on research of popular HuggingFace Spaces and industry trends (2025):

1. **Most Popular Open-Source TTS**: #1 trending on HuggingFace and GitHub
2. **Multilingual**: Supports 17 languages
3. **Voice Cloning**: Clone voice from just 6 seconds of audio
4. **Emotional Transfer**: Captures emotion and speaking style
5. **High Quality**: Natural-sounding speech output
6. **Cross-language**: Clone voice and speak in different language

## Supported Languages

XTTS-v2 supports 17 languages:
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Polish (pl)
- Turkish (tr)
- Russian (ru)
- Dutch (nl)
- Czech (cs)
- Arabic (ar)
- Chinese (zh-cn)
- Japanese (ja)
- Hungarian (hu)
- Korean (ko)
- Hindi (hi)

## Popular HuggingFace Spaces Using XTTS

### 1. coqui/xtts
- **Approach**: Server-side generation with GPU
- **Features**:
  - Voice cloning from uploaded audio
  - Multiple language support
  - Real-time generation
  - Streaming audio output

### 2. coqui/CoquiTTS
- **Approach**: Multi-model TTS platform
- **Features**:
  - Multiple TTS models available
  - XTTS-v2 as primary model
  - Voice management system

## Our Implementation: Server-Side with Python

We follow the **coqui/xtts** approach for high-quality, server-side TTS generation.

### Technology Stack

```python
# Core Libraries
from TTS.api import TTS
import torch

# Web Framework
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

# Audio Processing
import soundfile as sf
import io
```

### Model Specifications

**Model Name**: `tts_models/multilingual/multi-dataset/xtts_v2`

**Requirements**:
- GPU: Recommended (CUDA-capable)
- RAM: 8GB minimum
- Disk Space: ~2GB for model weights
- Python: 3.9+

**Performance**:
- Generation Speed: ~1-2s for short sentences (with GPU)
- Quality: Near-human natural speech
- Latency: Low for real-time applications

### Implementation Steps

#### 1. Backend Setup

```python
# backend/tts_engine.py

import torch
from TTS.api import TTS
import io
import soundfile as sf
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class XTTSEngine:
    """
    Text-to-Speech engine using Coqui XTTS-v2
    Following the implementation from huggingface.co/spaces/coqui/xtts
    """

    def __init__(self, model_name="tts_models/multilingual/multi-dataset/xtts_v2"):
        self.model_name = model_name
        self.tts = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.default_voice_path = None
        self.is_loaded = False

    def load_model(self):
        """Load the XTTS model into memory"""
        if self.is_loaded:
            logger.info("Model already loaded")
            return

        try:
            logger.info(f"Loading XTTS model on {self.device}...")

            # Initialize TTS with XTTS-v2
            self.tts = TTS(
                model_name=self.model_name,
                progress_bar=False,
                gpu=(self.device == "cuda")
            )

            # Move to device
            if self.device == "cuda":
                self.tts.to(self.device)

            self.is_loaded = True
            logger.info("XTTS model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load XTTS model: {e}")
            raise

    def synthesize(
        self,
        text: str,
        language: str = "en",
        speaker_wav: str = None,
        output_path: str = None
    ) -> bytes:
        """
        Synthesize speech from text

        Args:
            text: Text to convert to speech
            language: Language code (en, es, fr, etc.)
            speaker_wav: Path to speaker reference audio (for voice cloning)
            output_path: Optional path to save audio file

        Returns:
            Audio data as bytes (WAV format)
        """
        if not self.is_loaded:
            self.load_model()

        try:
            # Use default voice if none provided
            if speaker_wav is None:
                speaker_wav = self.default_voice_path or self._get_default_voice(language)

            logger.info(f"Synthesizing text in {language}: {text[:50]}...")

            # Generate speech
            # XTTS expects speaker_wav for voice cloning
            wav = self.tts.tts(
                text=text,
                speaker_wav=speaker_wav,
                language=language
            )

            # Convert to bytes
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
                logger.info(f"Audio saved to {output_path}")

            return audio_bytes

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            raise

    def synthesize_streaming(
        self,
        text: str,
        language: str = "en",
        speaker_wav: str = None,
        chunk_size: int = 4096
    ):
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

        logger.info(f"Cloning voice from {speaker_wav_path}")

        return self.synthesize(
            text=text,
            language=language,
            speaker_wav=speaker_wav_path
        )

    def _get_default_voice(self, language: str) -> str:
        """
        Get default voice for a language

        For production, you would have a library of preset voices
        For now, returns None and requires user to provide voice
        """
        # TODO: Implement default voice library
        default_voices = {
            "en": "voices/en_default.wav",
            "es": "voices/es_default.wav",
            # Add more default voices
        }

        return default_voices.get(language)

    def set_default_voice(self, voice_path: str):
        """Set the default voice for TTS"""
        if Path(voice_path).exists():
            self.default_voice_path = voice_path
            logger.info(f"Default voice set to {voice_path}")
        else:
            logger.error(f"Voice file not found: {voice_path}")
            raise FileNotFoundError(f"Voice file not found: {voice_path}")

    def get_supported_languages(self) -> list:
        """Return list of supported languages"""
        return [
            "en", "es", "fr", "de", "it", "pt", "pl", "tr",
            "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko", "hi"
        ]
```

#### 2. FastAPI Integration

```python
# backend/main.py

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
from pathlib import Path
import tempfile
import os

from tts_engine import XTTSEngine
from openai_integration import OpenAIClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Voice AI Agent API",
    description="Backend API for voice-enabled AI agent",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
tts_engine = XTTSEngine()
openai_client = OpenAIClient()

# Pydantic models
class ChatRequest(BaseModel):
    text: str
    enable_tts: bool = False
    language: str = "en"
    conversation_id: str = None

class ChatResponse(BaseModel):
    response_text: str
    conversation_id: str
    audio_url: str = None

class TTSRequest(BaseModel):
    text: str
    language: str = "en"
    voice_id: str = None

# Startup event
@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    logger.info("Starting Voice AI Agent API...")

    # Load TTS model
    try:
        tts_engine.load_model()
        logger.info("TTS engine loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load TTS engine: {e}")

    # Test OpenAI connection
    try:
        openai_client.test_connection()
        logger.info("OpenAI client connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to OpenAI: {e}")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "tts_loaded": tts_engine.is_loaded,
        "openai_connected": openai_client.is_connected()
    }

# Chat endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process chat request with optional TTS

    Args:
        request: Chat request with text and options

    Returns:
        Chat response with text and optional audio URL
    """
    try:
        logger.info(f"Chat request: {request.text[:50]}...")

        # Call OpenAI API
        response_text = await openai_client.get_completion(
            text=request.text,
            conversation_id=request.conversation_id
        )

        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or openai_client.create_conversation_id()

        response = ChatResponse(
            response_text=response_text,
            conversation_id=conversation_id
        )

        # Generate TTS if requested
        if request.enable_tts:
            # For simplicity, we'll include audio inline
            # In production, you might save to S3 and return URL
            response.audio_url = f"/api/tts/stream?text={response_text}&language={request.language}"

        return response

    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# TTS endpoint
@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech

    Args:
        request: TTS request with text and options

    Returns:
        Audio file as streaming response
    """
    try:
        logger.info(f"TTS request: {request.text[:50]}...")

        # Generate audio
        audio_bytes = tts_engine.synthesize(
            text=request.text,
            language=request.language
        )

        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=speech.wav"
            }
        )

    except Exception as e:
        logger.error(f"TTS request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# TTS streaming endpoint
@app.get("/api/tts/stream")
async def text_to_speech_stream(text: str, language: str = "en"):
    """
    Stream TTS audio

    Args:
        text: Text to convert
        language: Language code

    Returns:
        Streaming audio response
    """
    try:
        # Stream audio in chunks
        return StreamingResponse(
            tts_engine.synthesize_streaming(text, language),
            media_type="audio/wav"
        )

    except Exception as e:
        logger.error(f"TTS streaming failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Voice cloning endpoint
@app.post("/api/tts/clone-voice")
async def clone_voice(
    text: str = Form(...),
    language: str = Form("en"),
    voice_file: UploadFile = File(...)
):
    """
    Clone voice and generate speech

    Args:
        text: Text to speak
        language: Language code
        voice_file: Audio file with target voice (6+ seconds)

    Returns:
        Audio with cloned voice
    """
    try:
        logger.info(f"Voice cloning request for text: {text[:50]}...")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await voice_file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Clone voice and generate speech
        audio_bytes = tts_engine.clone_voice(
            text=text,
            speaker_wav_path=tmp_path,
            language=language
        )

        # Cleanup temp file
        os.unlink(tmp_path)

        # Return audio
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=cloned_speech.wav"
            }
        )

    except Exception as e:
        logger.error(f"Voice cloning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get supported languages
@app.get("/api/tts/languages")
async def get_supported_languages():
    """Get list of supported TTS languages"""
    return {
        "languages": tts_engine.get_supported_languages()
    }

# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

#### 3. OpenAI Integration

```python
# backend/openai_integration.py

import openai
import os
from typing import Optional, Dict, List
import logging
import uuid

logger = logging.getLogger(__name__)

class OpenAIClient:
    """
    OpenAI API client for chat completions
    """

    def __init__(self, api_key: str = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.conversations: Dict[str, List[Dict]] = {}

        if not self.api_key:
            raise ValueError("OpenAI API key not found")

        openai.api_key = self.api_key

    def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            openai.Model.list()
            return True
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if OpenAI client is connected"""
        return self.api_key is not None

    def create_conversation_id(self) -> str:
        """Create a new conversation ID"""
        return str(uuid.uuid4())

    async def get_completion(
        self,
        text: str,
        conversation_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Get chat completion from OpenAI

        Args:
            text: User message
            conversation_id: Optional conversation ID for context
            system_prompt: Optional system prompt
            temperature: Response randomness (0-1)
            max_tokens: Maximum response length

        Returns:
            AI response text
        """
        try:
            # Get or create conversation history
            if conversation_id and conversation_id in self.conversations:
                messages = self.conversations[conversation_id]
            else:
                messages = []
                if system_prompt:
                    messages.append({
                        "role": "system",
                        "content": system_prompt
                    })
                else:
                    messages.append({
                        "role": "system",
                        "content": "You are a helpful AI assistant."
                    })

            # Add user message
            messages.append({
                "role": "user",
                "content": text
            })

            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Extract response text
            response_text = response.choices[0].message.content

            # Add assistant response to history
            messages.append({
                "role": "assistant",
                "content": response_text
            })

            # Save conversation history
            if conversation_id:
                self.conversations[conversation_id] = messages

            logger.info(f"OpenAI completion successful: {response_text[:50]}...")

            return response_text

        except Exception as e:
            logger.error(f"OpenAI completion failed: {e}")
            raise

    def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]

    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history"""
        return self.conversations.get(conversation_id, [])
```

## Installation and Setup

### 1. Install Dependencies

```bash
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
openai==1.3.0
TTS==0.20.0
torch==2.1.0
soundfile==0.12.1
numpy==1.24.3
pydantic==2.4.2
```

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# .env
OPENAI_API_KEY=your_openai_api_key_here
TTS_MODEL=tts_models/multilingual/multi-dataset/xtts_v2
DEFAULT_LANGUAGE=en
DEFAULT_VOICE_PATH=voices/default_en.wav
```

### 3. Run Server

```bash
python backend/main.py
```

Server will start on `http://localhost:8000`

## Testing

### Test TTS Endpoint

```bash
# Using curl
curl -X POST "http://localhost:8000/api/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of the text to speech system.",
    "language": "en"
  }' \
  --output test_speech.wav
```

### Test Voice Cloning

```bash
# Using curl with file upload
curl -X POST "http://localhost:8000/api/tts/clone-voice" \
  -F "text=Hello from my cloned voice!" \
  -F "language=en" \
  -F "voice_file=@path/to/your/voice.wav" \
  --output cloned_speech.wav
```

## Performance Optimization

### 1. GPU Acceleration
- Ensure CUDA is installed and available
- TTS will automatically use GPU if available
- GPU reduces generation time from 10s to 1-2s

### 2. Model Caching
- Model is loaded once on startup
- Kept in memory for fast inference
- ~2GB memory footprint

### 3. Async Processing
- Use FastAPI's async capabilities
- Process multiple requests concurrently
- Implement request queue for high load

### 4. Audio Streaming
- Stream audio in chunks
- Reduce perceived latency
- Better user experience

## Production Considerations

### 1. Voice Library Management
```python
# Store default voices in database or file system
voices_dir = Path("voices")
voices_dir.mkdir(exist_ok=True)

# Organize by language
for lang in tts_engine.get_supported_languages():
    (voices_dir / lang).mkdir(exist_ok=True)
```

### 2. Caching Strategy
```python
# Cache frequently requested TTS outputs
from functools import lru_cache
import hashlib

def get_cache_key(text: str, language: str) -> str:
    return hashlib.md5(f"{text}:{language}".encode()).hexdigest()

# Implement file-based cache
cache_dir = Path("tts_cache")
```

### 3. Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/tts")
@limiter.limit("10/minute")
async def text_to_speech(request: Request, tts_request: TTSRequest):
    # ...
```

## Error Handling

```python
# Custom exception handling
class TTSError(Exception):
    pass

@app.exception_handler(TTSError)
async def tts_exception_handler(request: Request, exc: TTSError):
    return JSONResponse(
        status_code=500,
        content={
            "error": "TTS generation failed",
            "detail": str(exc)
        }
    )
```

## References

- Coqui XTTS Space: https://huggingface.co/spaces/coqui/xtts
- Coqui TTS GitHub: https://github.com/coqui-ai/TTS
- XTTS-v2 Model Card: https://huggingface.co/coqui/XTTS-v2
- FastAPI Documentation: https://fastapi.tiangolo.com/
