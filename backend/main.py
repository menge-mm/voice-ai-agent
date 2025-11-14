"""
Voice AI Agent - FastAPI Backend
Main application file
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn
import logging
from pathlib import Path
import tempfile
import os
import io
from dotenv import load_dotenv

from tts_engine import XTTSEngine
from openai_integration import OpenAIClient

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Voice AI Agent API",
    description="Backend API for voice-enabled AI agent with STT, OpenAI, and TTS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
tts_engine = None
openai_client = None

# Pydantic models
class ChatRequest(BaseModel):
    text: str = Field(..., description="User message text")
    enable_tts: bool = Field(default=False, description="Enable text-to-speech response")
    language: str = Field(default="en", description="Language code")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for context")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Response randomness")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "What is the weather today?",
                "enable_tts": True,
                "language": "en",
                "conversation_id": None,
                "temperature": 0.7
            }
        }


class ChatResponse(BaseModel):
    response_text: str = Field(..., description="AI response text")
    conversation_id: str = Field(..., description="Conversation ID")
    audio_url: Optional[str] = Field(default=None, description="URL for TTS audio if enabled")
    tokens_used: Optional[int] = Field(default=None, description="Estimated tokens used")


class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech")
    language: str = Field(default="en", description="Language code")
    voice_id: Optional[str] = Field(default=None, description="Voice ID or path")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello, how are you doing today?",
                "language": "en",
                "voice_id": None
            }
        }


class HealthResponse(BaseModel):
    status: str
    tts_loaded: bool
    openai_connected: bool
    device: str


class ConversationSummary(BaseModel):
    conversation_id: str
    message_count: int
    exchanges: int
    last_updated: Optional[str]


# Import typing for Optional
from typing import Optional


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize models and services on startup"""
    global tts_engine, openai_client

    logger.info("=" * 60)
    logger.info("Starting Voice AI Agent API...")
    logger.info("=" * 60)

    # Initialize TTS engine
    try:
        logger.info("Initializing TTS engine...")
        force_cpu = os.getenv("FORCE_CPU", "false").lower() == "true"
        tts_engine = XTTSEngine(force_cpu=force_cpu)

        # Set default voice if configured
        default_voice = os.getenv("DEFAULT_VOICE_PATH")
        if default_voice and Path(default_voice).exists():
            tts_engine.set_default_voice(default_voice)

        # Load model
        tts_engine.load_model()
        logger.info("✓ TTS engine initialized successfully")

    except Exception as e:
        logger.error(f"✗ Failed to initialize TTS engine: {e}")
        logger.warning("TTS will be unavailable")

    # Initialize OpenAI client
    try:
        logger.info("Initializing OpenAI client...")
        model = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
        openai_client = OpenAIClient(model=model)
        logger.info("✓ OpenAI client initialized successfully")

    except Exception as e:
        logger.error(f"✗ Failed to initialize OpenAI client: {e}")
        raise  # OpenAI is critical, so we raise the exception

    logger.info("=" * 60)
    logger.info("Voice AI Agent API is ready!")
    logger.info(f"Access docs at: http://localhost:{os.getenv('PORT', 8000)}/docs")
    logger.info("=" * 60)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Voice AI Agent API...")

    if tts_engine and tts_engine.is_loaded:
        tts_engine.unload_model()

    logger.info("✓ Shutdown complete")


# Health check endpoint
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        tts_loaded=tts_engine.is_loaded if tts_engine else False,
        openai_connected=openai_client.is_connected() if openai_client else False,
        device=tts_engine.device if tts_engine else "unknown"
    )


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
        logger.info(f"Chat request: '{request.text[:100]}...' (tts={request.enable_tts}, lang={request.language})")

        # Call OpenAI API
        response_text = await openai_client.get_completion(
            text=request.text,
            conversation_id=request.conversation_id,
            temperature=request.temperature
        )

        # Generate or use conversation ID
        conversation_id = request.conversation_id or openai_client.create_conversation_id()

        # Estimate tokens
        tokens_used = openai_client.estimate_tokens(request.text + response_text)

        response = ChatResponse(
            response_text=response_text,
            conversation_id=conversation_id,
            tokens_used=tokens_used
        )

        # Generate TTS if requested
        if request.enable_tts:
            # Return streaming TTS URL
            response.audio_url = (
                f"/api/tts/stream?"
                f"text={response_text[:500]}&"  # Limit for URL length
                f"language={request.language}"
            )

        logger.info(f"✓ Chat response generated ({tokens_used} tokens)")
        return response

    except Exception as e:
        logger.error(f"✗ Chat request failed: {e}")
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
    if not tts_engine or not tts_engine.is_loaded:
        raise HTTPException(status_code=503, detail="TTS engine not available")

    try:
        logger.info(f"TTS request: '{request.text[:100]}...' (lang={request.language})")

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
                "Content-Disposition": "attachment; filename=speech.wav",
                "Content-Length": str(len(audio_bytes))
            }
        )

    except ValueError as e:
        # Voice file not found or invalid parameters
        logger.error(f"✗ TTS request validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"✗ TTS request failed: {e}")
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
    if not tts_engine or not tts_engine.is_loaded:
        raise HTTPException(status_code=503, detail="TTS engine not available")

    try:
        logger.info(f"TTS streaming: '{text[:100]}...' (lang={language})")

        # Stream audio in chunks
        return StreamingResponse(
            tts_engine.synthesize_streaming(text, language),
            media_type="audio/wav"
        )

    except Exception as e:
        logger.error(f"✗ TTS streaming failed: {e}")
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
    if not tts_engine or not tts_engine.is_loaded:
        raise HTTPException(status_code=503, detail="TTS engine not available")

    try:
        logger.info(f"Voice cloning request: '{text[:100]}...' (lang={language})")

        # Validate file type
        allowed_types = ["audio/wav", "audio/mpeg", "audio/mp3", "audio/ogg", "audio/flac"]
        if voice_file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {allowed_types}"
            )

        # Check file size (max 10MB)
        max_size = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10")) * 1024 * 1024
        content = await voice_file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {max_size // (1024*1024)}MB"
            )

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Clone voice and generate speech
            audio_bytes = tts_engine.clone_voice(
                text=text,
                speaker_wav_path=tmp_path,
                language=language
            )

            # Return audio
            return StreamingResponse(
                io.BytesIO(audio_bytes),
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "attachment; filename=cloned_speech.wav",
                    "Content-Length": str(len(audio_bytes))
                }
            )

        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Voice cloning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Get supported languages
@app.get("/api/tts/languages")
async def get_supported_languages():
    """Get list of supported TTS languages"""
    if not tts_engine:
        raise HTTPException(status_code=503, detail="TTS engine not available")

    return {
        "languages": tts_engine.get_supported_languages()
    }


# Conversation management endpoints
@app.get("/api/conversation/{conversation_id}", response_model=ConversationSummary)
async def get_conversation(conversation_id: str):
    """Get conversation summary"""
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI client not available")

    summary = openai_client.get_conversation_summary(conversation_id)

    if summary["message_count"] == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationSummary(**summary)


@app.delete("/api/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history"""
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI client not available")

    openai_client.clear_conversation(conversation_id)

    return {"message": f"Conversation {conversation_id} cleared"}


@app.get("/api/conversations")
async def get_all_conversations():
    """Get all active conversations"""
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI client not available")

    return openai_client.get_all_conversations()


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Voice AI Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health"
    }


# Main entry point
if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "false").lower() == "true"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
