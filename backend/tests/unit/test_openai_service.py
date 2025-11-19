"""
Unit tests for OpenAI service (TDD - Tests written FIRST)

The OpenAI service will:
- Use AsyncOpenAI for non-blocking API calls
- Accept ConversationRepository for persistence
- Build message history from database
- Handle errors gracefully with proper exceptions
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.openai_service import OpenAIService


class TestOpenAIService:
    """Test suite for OpenAI service"""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock AsyncOpenAI client"""
        client = AsyncMock()
        # Mock the chat.completions.create response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "AI response text"
        mock_response.usage.total_tokens = 150
        client.chat.completions.create = AsyncMock(return_value=mock_response)
        return client

    @pytest.fixture
    def mock_repository(self):
        """Mock ConversationRepository"""
        repo = AsyncMock()
        repo.get_messages = AsyncMock(return_value=[])
        return repo

    @pytest.fixture
    def openai_service(self, mock_openai_client, mock_repository):
        """Create OpenAI service with mocked dependencies"""
        service = OpenAIService(
            openai_client=mock_openai_client,
            conversation_repo=mock_repository,
            model="gpt-4-turbo"
        )
        return service

    async def test_get_completion_simple(self, openai_service, mock_openai_client):
        """Test simple completion without conversation history"""
        response = await openai_service.get_completion(
            text="Hello AI",
            conversation_id=None
        )

        assert response == "AI response text"
        mock_openai_client.chat.completions.create.assert_called_once()

    async def test_get_completion_with_conversation_id(
        self,
        openai_service,
        mock_openai_client,
        mock_repository
    ):
        """Test completion with conversation history from database"""
        # Mock conversation history
        mock_messages = [
            MagicMock(role="user", content="Previous question"),
            MagicMock(role="assistant", content="Previous answer")
        ]
        mock_repository.get_messages.return_value = mock_messages

        response = await openai_service.get_completion(
            text="Follow-up question",
            conversation_id="conv-123"
        )

        assert response == "AI response text"
        # Verify repository was called
        mock_repository.get_messages.assert_called_once_with("conv-123")
        # Verify OpenAI was called with history
        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        assert len(messages) == 4  # system + 2 history + current

    async def test_get_completion_with_custom_system_prompt(
        self,
        openai_service,
        mock_openai_client
    ):
        """Test completion with custom system prompt"""
        custom_prompt = "You are a coding assistant"

        await openai_service.get_completion(
            text="Write code",
            system_prompt=custom_prompt
        )

        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        assert messages[0]['role'] == 'system'
        assert messages[0]['content'] == custom_prompt

    async def test_get_completion_with_temperature(
        self,
        openai_service,
        mock_openai_client
    ):
        """Test completion with custom temperature"""
        await openai_service.get_completion(
            text="Be creative",
            temperature=0.9
        )

        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args.kwargs['temperature'] == 0.9

    async def test_get_completion_with_max_tokens(
        self,
        openai_service,
        mock_openai_client
    ):
        """Test completion with max tokens limit"""
        await openai_service.get_completion(
            text="Short answer",
            max_tokens=100
        )

        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args.kwargs['max_tokens'] == 100

    async def test_get_completion_returns_token_count(
        self,
        openai_service,
        mock_openai_client
    ):
        """Test that completion returns token usage"""
        response, tokens = await openai_service.get_completion_with_tokens(
            text="Hello"
        )

        assert response == "AI response text"
        assert tokens == 150

    async def test_get_completion_handles_openai_error(
        self,
        openai_service,
        mock_openai_client
    ):
        """Test error handling for OpenAI API errors"""
        from openai import RateLimitError

        mock_openai_client.chat.completions.create.side_effect = RateLimitError(
            "Rate limit exceeded",
            response=MagicMock(status_code=429),
            body={}
        )

        with pytest.raises(Exception) as exc_info:
            await openai_service.get_completion(text="Hello")

        assert "rate limit" in str(exc_info.value).lower()

    async def test_get_completion_handles_authentication_error(
        self,
        openai_service,
        mock_openai_client
    ):
        """Test error handling for authentication errors"""
        from openai import AuthenticationError

        mock_openai_client.chat.completions.create.side_effect = AuthenticationError(
            "Invalid API key",
            response=MagicMock(status_code=401),
            body={}
        )

        with pytest.raises(Exception) as exc_info:
            await openai_service.get_completion(text="Hello")

        assert "authentication" in str(exc_info.value).lower()

    async def test_get_streaming_completion(self, openai_service, mock_openai_client):
        """Test streaming completion"""
        # Mock streaming response
        async def mock_stream():
            chunks = ["Hello", " ", "world"]
            for chunk in chunks:
                mock_chunk = MagicMock()
                mock_chunk.choices = [MagicMock()]
                mock_chunk.choices[0].delta.content = chunk
                yield mock_chunk

        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_stream()
        )

        full_response = ""
        async for chunk in openai_service.get_streaming_completion(text="Hello"):
            full_response += chunk

        assert full_response == "Hello world"

    async def test_build_messages_with_empty_history(self, openai_service):
        """Test message building with no conversation history"""
        messages = await openai_service._build_messages(
            text="Current message",
            conversation_id=None,
            system_prompt="System prompt"
        )

        assert len(messages) == 2  # system + current
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == "Current message"

    async def test_build_messages_with_history(
        self,
        openai_service,
        mock_repository
    ):
        """Test message building with conversation history"""
        mock_messages = [
            MagicMock(role="user", content="Q1"),
            MagicMock(role="assistant", content="A1"),
            MagicMock(role="user", content="Q2"),
            MagicMock(role="assistant", content="A2")
        ]
        mock_repository.get_messages.return_value = mock_messages

        messages = await openai_service._build_messages(
            text="Q3",
            conversation_id="conv-123"
        )

        # system + 4 history + current = 6
        assert len(messages) == 6
        assert messages[0]['role'] == 'system'
        assert messages[-1]['content'] == "Q3"

    async def test_default_system_prompt_for_voice(self, openai_service):
        """Test that default system prompt is optimized for voice"""
        messages = await openai_service._build_messages(
            text="Test",
            conversation_id=None
        )

        system_prompt = messages[0]['content']
        # Should mention voice/concise/conversational
        assert any(word in system_prompt.lower() for word in ['voice', 'concise', 'conversational'])

    async def test_estimate_tokens(self, openai_service):
        """Test token estimation"""
        text = "This is a test message"
        tokens = openai_service.estimate_tokens(text)

        # Rough approximation: ~4 chars per token
        assert tokens > 0
        assert tokens == len(text) // 4

    async def test_set_model(self, openai_service):
        """Test changing the model"""
        openai_service.set_model("gpt-3.5-turbo")
        assert openai_service.model == "gpt-3.5-turbo"

    async def test_set_system_prompt(self, openai_service):
        """Test updating default system prompt"""
        new_prompt = "You are a helpful assistant"
        openai_service.set_system_prompt(new_prompt)
        assert openai_service.default_system_prompt == new_prompt
