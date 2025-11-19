"""
Unit tests for Chat service (TDD - Tests written FIRST)

ChatService orchestrates:
- OpenAI service for completions
- TTS service for audio generation
- ConversationRepository for persistence
- Business logic for chat flow
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.chat_service import ChatService, ChatResponse


class TestChatService:
    """Test suite for ChatService"""

    @pytest.fixture
    def mock_openai_service(self):
        """Mock OpenAI service"""
        service = AsyncMock()
        service.get_completion.return_value = "AI response text"
        service.get_completion_with_tokens.return_value = ("AI response text", 150)
        return service

    @pytest.fixture
    def mock_tts_service(self):
        """Mock TTS service"""
        service = AsyncMock()
        service.synthesize.return_value = b"audio data"
        service.is_ready.return_value = True
        return service

    @pytest.fixture
    def mock_conversation_repo(self):
        """Mock ConversationRepository"""
        repo = AsyncMock()
        repo.get_or_create.return_value = MagicMock(id="conv-123", user_id=1)
        repo.add_messages.return_value = [MagicMock(), MagicMock()]
        return repo

    @pytest.fixture
    def chat_service(self, mock_openai_service, mock_tts_service, mock_conversation_repo):
        """Create ChatService with mocked dependencies"""
        return ChatService(
            openai_service=mock_openai_service,
            tts_service=mock_tts_service,
            conversation_repo=mock_conversation_repo
        )

    async def test_process_message_text_only(
        self,
        chat_service,
        mock_openai_service,
        mock_conversation_repo
    ):
        """Test processing message without TTS"""
        response = await chat_service.process_message(
            text="Hello AI",
            user_id=1,
            conversation_id="conv-123",
            generate_audio=False
        )

        assert isinstance(response, ChatResponse)
        assert response.text == "AI response text"
        assert response.audio is None
        assert response.conversation_id == "conv-123"

        # Verify services called correctly
        mock_openai_service.get_completion_with_tokens.assert_called_once()
        mock_conversation_repo.get_or_create.assert_called_once()
        mock_conversation_repo.add_messages.assert_called_once()

    async def test_process_message_with_audio(
        self,
        chat_service,
        mock_openai_service,
        mock_tts_service,
        mock_conversation_repo
    ):
        """Test processing message with TTS audio generation"""
        response = await chat_service.process_message(
            text="Hello AI",
            user_id=1,
            conversation_id="conv-123",
            generate_audio=True
        )

        assert response.text == "AI response text"
        assert response.audio == b"audio data"
        assert response.audio_format == "wav"

        # Verify TTS was called
        mock_tts_service.synthesize.assert_called_once_with(
            text="AI response text",
            language="en"
        )

    async def test_process_message_creates_conversation(
        self,
        chat_service,
        mock_conversation_repo
    ):
        """Test that conversation is created/retrieved"""
        await chat_service.process_message(
            text="First message",
            user_id=1,
            conversation_id="new-conv"
        )

        mock_conversation_repo.get_or_create.assert_called_once_with(
            conversation_id="new-conv",
            user_id=1,
            title=None
        )

    async def test_process_message_saves_messages(
        self,
        chat_service,
        mock_conversation_repo
    ):
        """Test that both user and AI messages are saved"""
        await chat_service.process_message(
            text="User message",
            user_id=1,
            conversation_id="conv-123"
        )

        # Should save user message and AI response
        call_args = mock_conversation_repo.add_messages.call_args
        messages = call_args.kwargs['messages']

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "User message"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "AI response text"

    async def test_process_message_includes_token_count(
        self,
        chat_service,
        mock_conversation_repo
    ):
        """Test that token usage is saved with AI message"""
        await chat_service.process_message(
            text="Count tokens",
            user_id=1,
            conversation_id="conv-123"
        )

        call_args = mock_conversation_repo.add_messages.call_args
        messages = call_args.kwargs['messages']
        ai_message = messages[1]

        assert "tokens_used" in ai_message
        assert ai_message["tokens_used"] == 150

    async def test_process_message_with_custom_temperature(
        self,
        chat_service,
        mock_openai_service
    ):
        """Test using custom temperature parameter"""
        await chat_service.process_message(
            text="Be creative",
            user_id=1,
            temperature=0.9
        )

        call_args = mock_openai_service.get_completion_with_tokens.call_args
        assert call_args.kwargs["temperature"] == 0.9

    async def test_process_message_with_custom_max_tokens(
        self,
        chat_service,
        mock_openai_service
    ):
        """Test using custom max_tokens parameter"""
        await chat_service.process_message(
            text="Short answer",
            user_id=1,
            max_tokens=100
        )

        call_args = mock_openai_service.get_completion_with_tokens.call_args
        assert call_args.kwargs["max_tokens"] == 100

    async def test_process_message_with_custom_language(
        self,
        chat_service,
        mock_tts_service
    ):
        """Test TTS with custom language"""
        await chat_service.process_message(
            text="Hola",
            user_id=1,
            generate_audio=True,
            language="es"
        )

        call_args = mock_tts_service.synthesize.call_args
        assert call_args.kwargs["language"] == "es"

    async def test_process_message_handles_openai_error(
        self,
        chat_service,
        mock_openai_service
    ):
        """Test error handling when OpenAI fails"""
        mock_openai_service.get_completion_with_tokens.side_effect = Exception("API error")

        with pytest.raises(Exception) as exc_info:
            await chat_service.process_message(
                text="Test",
                user_id=1
            )

        assert "API error" in str(exc_info.value)

    async def test_process_message_handles_tts_error(
        self,
        chat_service,
        mock_tts_service,
        mock_openai_service
    ):
        """Test that TTS errors don't break the response"""
        mock_tts_service.synthesize.side_effect = Exception("TTS error")

        # Should still return text response even if audio fails
        response = await chat_service.process_message(
            text="Test",
            user_id=1,
            generate_audio=True
        )

        assert response.text == "AI response text"
        assert response.audio is None
        assert response.error_message is not None

    async def test_chat_response_to_dict(self, chat_service):
        """Test ChatResponse serialization"""
        response = ChatResponse(
            text="Hello",
            conversation_id="conv-123",
            audio=b"audio",
            audio_format="wav",
            tokens_used=100
        )

        data = response.to_dict()

        assert data["text"] == "Hello"
        assert data["conversation_id"] == "conv-123"
        assert data["audio_format"] == "wav"
        assert data["tokens_used"] == 100
        # Audio should be base64 encoded
        assert isinstance(data["audio"], str)

    async def test_generate_conversation_title(
        self,
        chat_service,
        mock_openai_service
    ):
        """Test auto-generating conversation title from first message"""
        mock_openai_service.get_completion.return_value = "Weather Discussion"

        title = await chat_service.generate_conversation_title(
            first_message="What's the weather like?"
        )

        assert title == "Weather Discussion"
        # Should use specific prompt for title generation
        call_args = mock_openai_service.get_completion.call_args
        assert "title" in call_args.kwargs.get("system_prompt", "").lower()

    async def test_get_conversation_summary(
        self,
        chat_service,
        mock_conversation_repo
    ):
        """Test getting conversation summary"""
        mock_conversation_repo.get_messages.return_value = [
            MagicMock(role="user", content="Q1"),
            MagicMock(role="assistant", content="A1"),
            MagicMock(role="user", content="Q2"),
            MagicMock(role="assistant", content="A2"),
        ]

        summary = await chat_service.get_conversation_summary("conv-123")

        assert summary["message_count"] == 4
        assert summary["exchange_count"] == 2
        assert summary["conversation_id"] == "conv-123"

    async def test_delete_conversation(
        self,
        chat_service,
        mock_conversation_repo
    ):
        """Test deleting a conversation"""
        mock_conversation_repo.delete.return_value = True

        success = await chat_service.delete_conversation("conv-123")

        assert success is True
        mock_conversation_repo.delete.assert_called_once_with("conv-123")

    async def test_process_message_auto_generates_conversation_id(
        self,
        chat_service,
        mock_conversation_repo
    ):
        """Test that conversation_id is auto-generated if not provided"""
        response = await chat_service.process_message(
            text="First message",
            user_id=1,
            conversation_id=None
        )

        # Should generate a conversation ID
        assert response.conversation_id is not None
        assert isinstance(response.conversation_id, str)
        assert len(response.conversation_id) > 0
