"""
Chat endpoints

Handles chat interactions with OpenAI and optional TTS generation.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import logging

from app.services.chat_service import ChatService
from app.api.deps import get_chat_service

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "What is the weather today?",
                "user_id": 1,
                "generate_audio": False,
                "temperature": 0.7
            }
        }
    )

    text: str = Field(..., description="User message text", min_length=1)
    user_id: int = Field(..., description="User ID", gt=0)
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    generate_audio: bool = Field(False, description="Generate TTS audio")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Response randomness")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens in response")
    language: str = Field("en", description="Language for TTS")


class ChatResponseModel(BaseModel):
    """Chat response model"""
    text: str = Field(..., description="AI response text")
    conversation_id: str = Field(..., description="Conversation ID")
    audio: Optional[str] = Field(None, description="Base64-encoded audio if generated")
    tokens_used: Optional[int] = Field(None, description="Tokens used in this interaction")


@router.post("/chat", response_model=ChatResponseModel)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    Process chat message with optional TTS generation.

    Args:
        request: Chat request with text and options
        chat_service: Injected ChatService dependency

    Returns:
        ChatResponseModel with AI response, conversation_id, optional audio

    Raises:
        HTTPException: If chat processing fails
    """
    try:
        logger.info(
            f"Chat request from user {request.user_id}: "
            f"'{request.text[:100]}...' (audio={request.generate_audio})"
        )

        # Process chat message
        response = await chat_service.process_message(
            text=request.text,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            generate_audio=request.generate_audio,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            language=request.language,
        )

        logger.info(
            f"Chat response generated: conv_id={response.conversation_id}, "
            f"tokens={response.tokens_used}, audio={response.audio is not None}"
        )

        # Convert to API response format
        return ChatResponseModel(
            text=response.text,
            conversation_id=response.conversation_id,
            audio=response.to_dict().get("audio"),  # Base64-encoded if present
            tokens_used=response.tokens_used,
        )

    except ValueError as e:
        # Invalid parameters (e.g., unsupported language)
        logger.error(f"Chat validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Internal server error
        logger.error(f"Chat processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to process chat message. Please try again."
        )
