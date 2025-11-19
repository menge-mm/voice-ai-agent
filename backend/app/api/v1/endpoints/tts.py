"""
TTS (Text-to-Speech) endpoints

Handles text-to-speech synthesis.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import logging
import io

from app.services.tts_service import TTSService
from app.api.deps import get_tts_service

logger = logging.getLogger(__name__)

router = APIRouter()


class TTSRequest(BaseModel):
    """TTS request model"""
    text: str = Field(..., description="Text to convert to speech", min_length=1, max_length=5000)
    language: str = Field("en", description="Language code (e.g., 'en', 'es', 'fr')")


@router.post("/tts")
async def text_to_speech(
    request: TTSRequest,
    tts_service: TTSService = Depends(get_tts_service),
):
    """
    Convert text to speech (WAV audio).

    Args:
        request: TTS request with text and language
        tts_service: Injected TTSService dependency

    Returns:
        StreamingResponse with WAV audio

    Raises:
        HTTPException: If TTS synthesis fails
    """
    try:
        logger.info(f"TTS request: '{request.text[:100]}...' (lang={request.language})")

        # Synthesize audio
        audio_bytes = await tts_service.synthesize(
            text=request.text,
            language=request.language,
        )

        logger.info(f"TTS synthesis complete: {len(audio_bytes)} bytes")

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
        # Invalid parameters (e.g., unsupported language)
        logger.error(f"TTS validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Internal server error
        logger.error(f"TTS synthesis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to synthesize speech. Please try again."
        )
