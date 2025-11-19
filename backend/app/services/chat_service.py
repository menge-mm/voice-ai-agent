"""
Chat Service - Orchestration layer for AI conversations

This service coordinates OpenAI, TTS, and database persistence
to provide complete chat functionality with optional audio.
"""

import logging
import uuid
import base64
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ChatResponse:
    """
    Response from chat service containing text, audio, and metadata.

    Attributes:
        text: AI response text
        conversation_id: ID of the conversation
        audio: Audio bytes (WAV format) if generated
        audio_format: Audio format (default: wav)
        tokens_used: Number of tokens consumed
        error_message: Error message if something failed
    """
    text: str
    conversation_id: str
    audio: Optional[bytes] = None
    audio_format: str = "wav"
    tokens_used: Optional[int] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = {
            "text": self.text,
            "conversation_id": self.conversation_id,
            "audio_format": self.audio_format,
            "tokens_used": self.tokens_used,
        }

        # Base64 encode audio if present
        if self.audio:
            data["audio"] = base64.b64encode(self.audio).decode("utf-8")
        else:
            data["audio"] = None

        if self.error_message:
            data["error_message"] = self.error_message

        return data


class ChatService:
    """
    Chat service for orchestrating AI conversations.

    Coordinates:
    - OpenAI service for completions
    - TTS service for audio generation
    - ConversationRepository for persistence

    Example:
        ```python
        chat = ChatService(openai_service, tts_service, conversation_repo)

        response = await chat.process_message(
            text="Hello AI",
            user_id=1,
            generate_audio=True
        )

        print(response.text)
        save_audio(response.audio)
        ```
    """

    def __init__(
        self,
        openai_service,
        tts_service,
        conversation_repo
    ):
        """
        Initialize chat service.

        Args:
            openai_service: OpenAI service instance
            tts_service: TTS service instance
            conversation_repo: ConversationRepository instance
        """
        self.openai_service = openai_service
        self.tts_service = tts_service
        self.conversation_repo = conversation_repo

    async def process_message(
        self,
        text: str,
        user_id: int,
        conversation_id: Optional[str] = None,
        generate_audio: bool = False,
        language: str = "en",
        temperature: float = 0.7,
        max_tokens: int = 500,
        auto_title: bool = False
    ) -> ChatResponse:
        """
        Process a user message and generate AI response.

        Args:
            text: User message text
            user_id: ID of the user
            conversation_id: Optional conversation ID (auto-generated if None)
            generate_audio: Whether to generate TTS audio
            language: Language for TTS (default: en)
            temperature: OpenAI temperature parameter
            max_tokens: OpenAI max_tokens parameter
            auto_title: Auto-generate conversation title from first message

        Returns:
            ChatResponse with text, audio, and metadata

        Raises:
            Exception: If OpenAI or database operations fail
        """
        try:
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                logger.info(f"Generated new conversation ID: {conversation_id}")

            # Ensure conversation exists in database
            conversation = await self.conversation_repo.get_or_create(
                conversation_id=conversation_id,
                user_id=user_id,
                title=None
            )

            # Get AI completion with token count
            ai_response, tokens_used = await self.openai_service.get_completion_with_tokens(
                text=text,
                conversation_id=conversation_id,
                temperature=temperature,
                max_tokens=max_tokens
            )

            logger.info(f"✓ AI response generated: {len(ai_response)} chars, {tokens_used} tokens")

            # Save messages to database
            messages = [
                {
                    "role": "user",
                    "content": text
                },
                {
                    "role": "assistant",
                    "content": ai_response,
                    "tokens_used": tokens_used
                }
            ]

            await self.conversation_repo.add_messages(
                conversation_id=conversation_id,
                messages=messages
            )

            logger.info(f"✓ Messages saved to conversation {conversation_id}")

            # Generate audio if requested
            audio_bytes = None
            error_message = None

            if generate_audio:
                try:
                    audio_bytes = await self.tts_service.synthesize(
                        text=ai_response,
                        language=language
                    )
                    logger.info(f"✓ Audio generated: {len(audio_bytes)} bytes")
                except Exception as e:
                    logger.error(f"✗ TTS generation failed: {e}")
                    error_message = f"Audio generation failed: {str(e)}"

            # Auto-generate title if this is first message
            if auto_title:
                try:
                    title = await self.generate_conversation_title(text)
                    await self.conversation_repo.update(
                        conversation_id,
                        {"title": title}
                    )
                except Exception as e:
                    logger.warning(f"Failed to generate title: {e}")

            return ChatResponse(
                text=ai_response,
                conversation_id=conversation_id,
                audio=audio_bytes,
                audio_format="wav",
                tokens_used=tokens_used,
                error_message=error_message
            )

        except Exception as e:
            logger.error(f"✗ Chat processing failed: {e}")
            raise

    async def generate_conversation_title(
        self,
        first_message: str,
        max_length: int = 50
    ) -> str:
        """
        Generate a conversation title from the first message.

        Args:
            first_message: First user message in conversation
            max_length: Maximum title length

        Returns:
            Generated title
        """
        system_prompt = f"""Generate a short, descriptive title for a conversation that starts with this message.
The title should be {max_length} characters or less, descriptive, and capture the main topic.
Return ONLY the title, nothing else."""

        title = await self.openai_service.get_completion(
            text=first_message,
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=20
        )

        # Clean up title
        title = title.strip().strip('"\'').strip()

        # Truncate if needed
        if len(title) > max_length:
            title = title[:max_length].strip()

        return title

    async def get_conversation_summary(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Get summary of a conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            Dictionary with conversation statistics
        """
        messages = await self.conversation_repo.get_messages(conversation_id)

        return {
            "conversation_id": conversation_id,
            "message_count": len(messages),
            "exchange_count": len(messages) // 2,
            "has_messages": len(messages) > 0
        }

    async def delete_conversation(
        self,
        conversation_id: str
    ) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: ID of the conversation to delete

        Returns:
            True if deleted, False if not found
        """
        success = await self.conversation_repo.delete(conversation_id)

        if success:
            logger.info(f"✓ Deleted conversation {conversation_id}")
        else:
            logger.warning(f"Conversation {conversation_id} not found")

        return success
