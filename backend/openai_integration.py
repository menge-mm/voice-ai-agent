"""
OpenAI API Integration for Chat Completions
"""

from openai import OpenAI
import os
from typing import Optional, Dict, List, AsyncGenerator
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    OpenAI API client for chat completions with conversation management
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo",
        default_system_prompt: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. "
                "Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )

        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.conversations: Dict[str, List[Dict]] = {}
        self.default_system_prompt = default_system_prompt or self._get_default_system_prompt()
        self._test_connection()

    def _get_default_system_prompt(self) -> str:
        """Default system prompt optimized for voice conversations"""
        return """You are a helpful, friendly AI assistant engaged in a voice conversation.

Keep your responses:
- Concise and conversational (1-3 sentences typically)
- Natural and easy to understand when spoken aloud
- Avoid special characters, formatting, or lists when possible
- Use simple language suitable for text-to-speech

Remember you're having a voice conversation, so speak naturally!"""

    def _test_connection(self):
        """Test OpenAI API connection on initialization"""
        try:
            self.client.models.list()
            logger.info("✓ OpenAI API connection successful")
        except Exception as e:
            logger.error(f"✗ OpenAI connection test failed: {e}")
            raise

    def is_connected(self) -> bool:
        """Check if OpenAI client is configured"""
        return self.api_key is not None

    def create_conversation_id(self) -> str:
        """Create a new unique conversation ID"""
        return str(uuid.uuid4())

    async def get_completion(
        self,
        text: str,
        conversation_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        stream: bool = False
    ) -> str:
        """
        Get chat completion from OpenAI

        Args:
            text: User message
            conversation_id: Optional conversation ID for context
            system_prompt: Optional custom system prompt
            temperature: Response randomness (0-1)
            max_tokens: Maximum response length
            stream: Whether to stream the response

        Returns:
            AI response text
        """
        try:
            # Build message history
            messages = self._build_messages(
                text=text,
                conversation_id=conversation_id,
                system_prompt=system_prompt
            )

            logger.info(f"Requesting OpenAI completion for: {text[:50]}...")

            # Call OpenAI API (v1 API)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Extract response
            response_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            # Update conversation history
            if conversation_id:
                self._add_to_conversation(conversation_id, "user", text)
                self._add_to_conversation(conversation_id, "assistant", response_text)

            logger.info(f"✓ OpenAI completion: {len(response_text)} chars, {tokens_used} tokens")

            return response_text

        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower():
                logger.error(f"✗ OpenAI rate limit exceeded: {e}")
                raise Exception("API rate limit exceeded. Please try again later.")
            elif "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                logger.error(f"✗ OpenAI authentication failed: {e}")
                raise Exception("API authentication failed. Check your API key.")
            elif "invalid" in error_msg.lower():
                logger.error(f"✗ OpenAI invalid request: {e}")
                raise Exception(f"Invalid request to OpenAI API: {e}")
            else:
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
        Get streaming chat completion from OpenAI

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
            messages = self._build_messages(text, conversation_id, system_prompt)

            logger.info(f"Requesting OpenAI streaming completion for: {text[:50]}...")

            # Create streaming completion (v1 API)
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            # Collect full response for history
            full_response = ""

            # Yield chunks
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content

            # Update conversation history
            if conversation_id:
                self._add_to_conversation(conversation_id, "user", text)
                self._add_to_conversation(conversation_id, "assistant", full_response)

            logger.info(f"✓ Streaming complete: {len(full_response)} chars")

        except Exception as e:
            logger.error(f"✗ OpenAI streaming failed: {e}")
            raise

    def _build_messages(
        self,
        text: str,
        conversation_id: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> List[Dict]:
        """Build message list for OpenAI API"""

        # Start with system prompt
        messages = [{
            "role": "system",
            "content": system_prompt or self.default_system_prompt
        }]

        # Add conversation history if exists
        if conversation_id and conversation_id in self.conversations:
            # Add only the role and content, not timestamp
            for msg in self.conversations[conversation_id]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add current user message
        messages.append({
            "role": "user",
            "content": text
        })

        return messages

    def _add_to_conversation(
        self,
        conversation_id: str,
        role: str,
        content: str
    ):
        """Add message to conversation history"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        self.conversations[conversation_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

        # Limit history to last N messages
        max_history = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))
        if len(self.conversations[conversation_id]) > max_history:
            self.conversations[conversation_id] = self.conversations[conversation_id][-max_history:]

    def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"✓ Cleared conversation {conversation_id}")

    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history"""
        return self.conversations.get(conversation_id, [])

    def get_conversation_summary(self, conversation_id: str) -> Dict:
        """Get summary of conversation"""
        history = self.get_conversation_history(conversation_id)

        return {
            "conversation_id": conversation_id,
            "message_count": len(history),
            "exchanges": len(history) // 2,
            "last_updated": history[-1]["timestamp"] if history else None
        }

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        Simple approximation: ~4 chars per token
        """
        return len(text) // 4

    def set_model(self, model: str):
        """Change the OpenAI model"""
        valid_models = [
            "gpt-4",
            "gpt-4-32k",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]

        if model in valid_models:
            self.model = model
            logger.info(f"✓ Model changed to {model}")
        else:
            logger.warning(f"Model '{model}' not in validated list, but setting anyway")
            self.model = model

    def set_system_prompt(self, prompt: str):
        """Update default system prompt"""
        self.default_system_prompt = prompt
        logger.info("✓ System prompt updated")

    def get_all_conversations(self) -> Dict[str, Dict]:
        """Get summary of all active conversations"""
        return {
            conv_id: self.get_conversation_summary(conv_id)
            for conv_id in self.conversations.keys()
        }

    def cleanup_old_conversations(self, max_age_minutes: int = 30):
        """Remove old conversations"""
        from datetime import datetime, timedelta

        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        to_remove = []

        for conv_id, messages in self.conversations.items():
            if messages:
                last_msg_time = datetime.fromisoformat(messages[-1]["timestamp"])
                if last_msg_time < cutoff_time:
                    to_remove.append(conv_id)

        for conv_id in to_remove:
            del self.conversations[conv_id]
            logger.info(f"✓ Removed old conversation {conv_id}")

        if to_remove:
            logger.info(f"✓ Cleaned up {len(to_remove)} old conversations")
