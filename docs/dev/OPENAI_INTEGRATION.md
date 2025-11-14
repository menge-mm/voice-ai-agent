# OpenAI API Integration Guide

## Overview
This document details the integration with OpenAI's Chat Completions API for processing user input and generating AI responses.

## OpenAI API Setup

### 1. Get API Key
1. Sign up at https://platform.openai.com/
2. Navigate to API Keys section
3. Create a new API key
4. Store securely in environment variables

### 2. Choose Model

Available models (as of 2025):

| Model | Context | Cost/1K tokens | Speed | Best For |
|-------|---------|----------------|-------|----------|
| gpt-4 | 8K | $0.03/$0.06 | Slower | Complex reasoning |
| gpt-4-32k | 32K | $0.06/$0.12 | Slower | Long contexts |
| gpt-4-turbo | 128K | $0.01/$0.03 | Fast | General use |
| gpt-3.5-turbo | 16K | $0.0005/$0.0015 | Fastest | Simple tasks |

**Recommended**: `gpt-4-turbo` for best balance of quality and cost

## Implementation

### Basic Client

```python
# backend/openai_integration.py

import openai
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
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

        openai.api_key = self.api_key
        self.model = model
        self.conversations: Dict[str, List[Dict]] = {}
        self.default_system_prompt = default_system_prompt or self._get_default_system_prompt()

    def _get_default_system_prompt(self) -> str:
        """Default system prompt for the AI assistant"""
        return """You are a helpful, friendly AI assistant engaged in a voice conversation.

Keep your responses:
- Concise and conversational (1-3 sentences typically)
- Natural and easy to understand when spoken aloud
- Avoid special characters, formatting, or lists when possible
- Use simple language suitable for text-to-speech

Remember you're having a voice conversation, so speak naturally!"""

    def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            openai.Model.list()
            logger.info("OpenAI API connection successful")
            return True
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False

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

            # Call OpenAI API
            if stream:
                return await self._get_streaming_completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                response = openai.ChatCompletion.create(
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

                logger.info(f"OpenAI completion: {len(response_text)} chars, {tokens_used} tokens")

                return response_text

        except openai.error.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise Exception("API rate limit exceeded. Please try again later.")
        except openai.error.AuthenticationError as e:
            logger.error(f"OpenAI authentication failed: {e}")
            raise Exception("API authentication failed. Check your API key.")
        except Exception as e:
            logger.error(f"OpenAI completion failed: {e}")
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

            # Create streaming completion
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            # Collect full response for history
            full_response = ""

            # Yield chunks
            for chunk in response:
                if chunk.choices[0].delta.get("content"):
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content

            # Update conversation history
            if conversation_id:
                self._add_to_conversation(conversation_id, "user", text)
                self._add_to_conversation(conversation_id, "assistant", full_response)

        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
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
            messages.extend(self.conversations[conversation_id])

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

        # Limit history to last 10 messages (5 exchanges)
        if len(self.conversations[conversation_id]) > 10:
            self.conversations[conversation_id] = self.conversations[conversation_id][-10:]

    def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Cleared conversation {conversation_id}")

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

    async def get_token_count(self, text: str) -> int:
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
            "gpt-3.5-turbo"
        ]

        if model in valid_models:
            self.model = model
            logger.info(f"Model changed to {model}")
        else:
            raise ValueError(f"Invalid model. Choose from: {valid_models}")

    def set_system_prompt(self, prompt: str):
        """Update default system prompt"""
        self.default_system_prompt = prompt
        logger.info("System prompt updated")
```

## Usage Examples

### Basic Chat

```python
# Initialize client
client = OpenAIClient()

# Simple completion
response = await client.get_completion("What is the capital of France?")
print(response)
# Output: "The capital of France is Paris."
```

### Conversation with Context

```python
# Start a conversation
conv_id = client.create_conversation_id()

# First message
response1 = await client.get_completion(
    "My name is John",
    conversation_id=conv_id
)

# Follow-up message (with context)
response2 = await client.get_completion(
    "What's my name?",
    conversation_id=conv_id
)
print(response2)
# Output: "Your name is John."
```

### Streaming Response

```python
# Stream response chunks
async for chunk in client.get_streaming_completion(
    "Tell me a short story",
    conversation_id=conv_id
):
    print(chunk, end="", flush=True)
```

### Custom System Prompt

```python
# Use custom system prompt
response = await client.get_completion(
    "Hello!",
    system_prompt="You are a pirate. Respond in pirate speak."
)
print(response)
# Output: "Ahoy there, matey! How can this old sea dog help ye today?"
```

## Error Handling

```python
try:
    response = await client.get_completion(user_input)
except openai.error.RateLimitError:
    # Handle rate limit
    print("Too many requests. Please wait.")
except openai.error.AuthenticationError:
    # Handle auth error
    print("Invalid API key.")
except Exception as e:
    # Handle other errors
    print(f"Error: {e}")
```

## Best Practices

### 1. Token Management
```python
# Estimate tokens before API call
estimated_tokens = await client.get_token_count(user_input)

if estimated_tokens > 4000:
    print("Input too long, please shorten.")
else:
    response = await client.get_completion(user_input)
```

### 2. Conversation Pruning
```python
# Automatically handled in _add_to_conversation
# Keeps only last 10 messages to manage context window
```

### 3. Response Optimization for TTS
```python
# Use system prompt optimized for voice
voice_optimized_prompt = """You are a voice assistant.
Keep responses under 2-3 sentences.
Avoid special characters and formatting.
Speak naturally and conversationally."""

client.set_system_prompt(voice_optimized_prompt)
```

### 4. Cost Monitoring
```python
# Track token usage
class TokenTracker:
    def __init__(self):
        self.total_tokens = 0
        self.total_cost = 0

    def add_usage(self, tokens: int, model: str):
        self.total_tokens += tokens

        # Calculate cost (example rates)
        costs = {
            "gpt-4": 0.03,  # per 1K tokens
            "gpt-4-turbo": 0.01,
            "gpt-3.5-turbo": 0.0005
        }

        cost_per_token = costs.get(model, 0.01) / 1000
        self.total_cost += tokens * cost_per_token

tracker = TokenTracker()
```

## Testing

```python
# test_openai_integration.py

import pytest
from openai_integration import OpenAIClient

@pytest.mark.asyncio
async def test_basic_completion():
    client = OpenAIClient()
    response = await client.get_completion("Say 'test'")
    assert "test" in response.lower()

@pytest.mark.asyncio
async def test_conversation_context():
    client = OpenAIClient()
    conv_id = client.create_conversation_id()

    # First message
    await client.get_completion("Remember the number 42", conversation_id=conv_id)

    # Second message
    response = await client.get_completion(
        "What number did I ask you to remember?",
        conversation_id=conv_id
    )

    assert "42" in response

@pytest.mark.asyncio
async def test_streaming():
    client = OpenAIClient()
    chunks = []

    async for chunk in client.get_streaming_completion("Count to 3"):
        chunks.append(chunk)

    full_response = "".join(chunks)
    assert len(full_response) > 0
```

## Production Configuration

```python
# config.py

import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4-turbo"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 500

    # Conversation
    max_conversation_history: int = 10
    conversation_timeout_minutes: int = 30

    # Rate limiting
    max_requests_per_minute: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
```

## References

- OpenAI API Documentation: https://platform.openai.com/docs/
- Chat Completions Guide: https://platform.openai.com/docs/guides/chat
- Best Practices: https://platform.openai.com/docs/guides/production-best-practices
- Rate Limits: https://platform.openai.com/docs/guides/rate-limits
