"""
OpenAI Service for chat completions with database persistence

This service integrates AsyncOpenAI with ConversationRepository
for production-ready, async, database-backed conversations.
"""

import logging
from typing import Optional, List, Dict, AsyncGenerator, Tuple
from openai import AsyncOpenAI, RateLimitError, AuthenticationError, APIError

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    OpenAI service for chat completions with conversation management.

    This service uses AsyncOpenAI for non-blocking API calls and
    ConversationRepository for persistent conversation storage.

    Example:
        ```python
        service = OpenAIService(
            openai_client=async_openai_client,
            conversation_repo=conversation_repo
        )

        response = await service.get_completion(
            text="Hello AI",
            conversation_id="conv-123"
        )
        ```
    """

    def __init__(
        self,
        openai_client: AsyncOpenAI,
        conversation_repo,  # Type hint would be circular import
        model: str = "gpt-4-turbo",
        default_system_prompt: Optional[str] = None
    ):
        """
        Initialize OpenAI service.

        Args:
            openai_client: Async OpenAI client instance
            conversation_repo: ConversationRepository for database access
            model: OpenAI model to use (default: gpt-4-turbo)
            default_system_prompt: Custom system prompt (optional)
        """
        self.client = openai_client
        self.conversation_repo = conversation_repo
        self.model = model
        self.default_system_prompt = default_system_prompt or self._get_default_system_prompt()

    def _get_default_system_prompt(self) -> str:
        """Default system prompt optimized for voice conversations"""
        return """You are a helpful, friendly AI assistant engaged in a voice conversation.

Keep your responses:
- Concise and conversational (1-3 sentences typically)
- Natural and easy to understand when spoken aloud
- Avoid special characters, formatting, or lists when possible
- Use simple language suitable for text-to-speech

Remember you're having a voice conversation, so speak naturally!"""

    async def get_completion(
        self,
        text: str,
        conversation_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Get chat completion from OpenAI.

        Args:
            text: User message
            conversation_id: Optional conversation ID for context
            system_prompt: Optional custom system prompt
            temperature: Response randomness (0-1)
            max_tokens: Maximum response length

        Returns:
            AI response text

        Raises:
            Exception: For rate limits, authentication errors, etc.
        """
        try:
            messages = await self._build_messages(
                text=text,
                conversation_id=conversation_id,
                system_prompt=system_prompt
            )

            logger.info(f"Requesting OpenAI completion for: {text[:50]}...")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            response_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            logger.info(f"✓ OpenAI completion: {len(response_text)} chars, {tokens_used} tokens")

            return response_text

        except RateLimitError as e:
            logger.error(f"✗ OpenAI rate limit exceeded: {e}")
            raise Exception("API rate limit exceeded. Please try again later.")
        except AuthenticationError as e:
            logger.error(f"✗ OpenAI authentication failed: {e}")
            raise Exception("API authentication failed. Check your API key.")
        except APIError as e:
            logger.error(f"✗ OpenAI API error: {e}")
            raise Exception(f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"✗ OpenAI completion failed: {e}")
            raise

    async def get_completion_with_tokens(
        self,
        text: str,
        conversation_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Tuple[str, int]:
        """
        Get chat completion with token count.

        Args:
            text: User message
            conversation_id: Optional conversation ID
            system_prompt: Optional custom system prompt
            temperature: Response randomness
            max_tokens: Maximum response length

        Returns:
            Tuple of (response_text, tokens_used)
        """
        try:
            messages = await self._build_messages(
                text=text,
                conversation_id=conversation_id,
                system_prompt=system_prompt
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            response_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            return (response_text, tokens_used)

        except Exception as e:
            logger.error(f"✗ OpenAI completion failed: {e}")
            raise

    async def get_streaming_completion(
        self,
        text: str,
        conversation_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> AsyncGenerator[str, None]:
        """
        Get streaming chat completion from OpenAI.

        Args:
            text: User message
            conversation_id: Optional conversation ID
            system_prompt: Optional custom system prompt
            temperature: Response randomness
            max_tokens: Maximum response length

        Yields:
            Response text chunks
        """
        try:
            messages = await self._build_messages(
                text=text,
                conversation_id=conversation_id,
                system_prompt=system_prompt
            )

            logger.info(f"Requesting OpenAI streaming completion for: {text[:50]}...")

            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            logger.info("✓ Streaming complete")

        except Exception as e:
            logger.error(f"✗ OpenAI streaming failed: {e}")
            raise

    async def _build_messages(
        self,
        text: str,
        conversation_id: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Build message list for OpenAI API.

        Loads conversation history from database if conversation_id provided.

        Args:
            text: Current user message
            conversation_id: Optional conversation ID to load history
            system_prompt: Optional custom system prompt

        Returns:
            List of message dictionaries for OpenAI API
        """
        # Start with system prompt
        messages = [{
            "role": "system",
            "content": system_prompt or self.default_system_prompt
        }]

        # Load conversation history from database
        if conversation_id:
            db_messages = await self.conversation_repo.get_messages(conversation_id)
            for msg in db_messages:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Add current user message
        messages.append({
            "role": "user",
            "content": text
        })

        return messages

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Simple approximation: ~4 characters per token

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def set_model(self, model: str):
        """
        Change the OpenAI model.

        Args:
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")
        """
        self.model = model
        logger.info(f"✓ Model changed to {model}")

    def set_system_prompt(self, prompt: str):
        """
        Update default system prompt.

        Args:
            prompt: New system prompt
        """
        self.default_system_prompt = prompt
        logger.info("✓ System prompt updated")
