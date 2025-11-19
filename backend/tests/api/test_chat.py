"""
API tests for chat endpoint (TDD - Tests written FIRST)

Tests chat functionality with OpenAI integration and optional TTS.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.services.chat_service import ChatResponse


class TestChatEndpoint:
    """Tests for POST /api/v1/chat endpoint"""

    @pytest.mark.asyncio
    async def test_chat_returns_200(self, test_app: FastAPI, mock_chat_service):
        """Test that chat endpoint returns 200 OK"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={"text": "Hello", "user_id": 1}
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_chat_returns_json(self, test_app: FastAPI, mock_chat_service):
        """Test that chat endpoint returns JSON"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={"text": "Hello", "user_id": 1}
            )
            assert response.headers["content-type"] == "application/json"

    @pytest.mark.asyncio
    async def test_chat_requires_text(self, test_app: FastAPI):
        """Test that text field is required"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={"user_id": 1}
            )
            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_chat_requires_user_id(self, test_app: FastAPI):
        """Test that user_id field is required"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={"text": "Hello"}
            )
            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_chat_response_includes_text(self, test_app: FastAPI, mock_chat_service):
        """Test that response includes AI text"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={"text": "Hello", "user_id": 1}
            )
            data = response.json()
            assert "text" in data
            assert isinstance(data["text"], str)

    @pytest.mark.asyncio
    async def test_chat_response_includes_conversation_id(self, test_app: FastAPI, mock_chat_service):
        """Test that response includes conversation_id"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={"text": "Hello", "user_id": 1}
            )
            data = response.json()
            assert "conversation_id" in data
            assert isinstance(data["conversation_id"], str)

    @pytest.mark.asyncio
    async def test_chat_calls_chat_service(self, test_app: FastAPI, mock_chat_service):
        """Test that chat endpoint calls ChatService.process_message"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            await client.post(
                "/api/v1/chat",
                json={"text": "Hello", "user_id": 1}
            )

            # Verify service was called with correct parameters
            mock_chat_service.process_message.assert_called_once()
            call_args = mock_chat_service.process_message.call_args
            assert call_args.kwargs["text"] == "Hello"
            assert call_args.kwargs["user_id"] == 1

    @pytest.mark.asyncio
    async def test_chat_with_conversation_id(self, test_app: FastAPI, mock_chat_service):
        """Test chat with existing conversation_id"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={
                    "text": "Continue chat",
                    "user_id": 1,
                    "conversation_id": "conv-123"
                }
            )
            assert response.status_code == 200

            # Verify conversation_id was passed to service
            call_args = mock_chat_service.process_message.call_args
            assert call_args.kwargs["conversation_id"] == "conv-123"

    @pytest.mark.asyncio
    async def test_chat_with_audio_generation(self, test_app: FastAPI, mock_chat_service):
        """Test chat with audio generation enabled"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={
                    "text": "Hello",
                    "user_id": 1,
                    "generate_audio": True
                }
            )
            assert response.status_code == 200

            # Verify audio generation was requested
            call_args = mock_chat_service.process_message.call_args
            assert call_args.kwargs["generate_audio"] is True

            # Response should include audio
            data = response.json()
            assert "audio" in data

    @pytest.mark.asyncio
    async def test_chat_without_audio_generation(self, test_app: FastAPI, mock_chat_service):
        """Test chat without audio generation"""
        # Mock service to return no audio
        mock_chat_service.process_message.return_value = ChatResponse(
            text="Hello!",
            conversation_id="conv-123",
            audio=None,
            tokens_used=25
        )

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={
                    "text": "Hello",
                    "user_id": 1,
                    "generate_audio": False
                }
            )
            assert response.status_code == 200

            data = response.json()
            assert data.get("audio") is None

    @pytest.mark.asyncio
    async def test_chat_with_custom_temperature(self, test_app: FastAPI, mock_chat_service):
        """Test chat with custom temperature"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            await client.post(
                "/api/v1/chat",
                json={
                    "text": "Hello",
                    "user_id": 1,
                    "temperature": 0.9
                }
            )

            call_args = mock_chat_service.process_message.call_args
            assert call_args.kwargs["temperature"] == 0.9

    @pytest.mark.asyncio
    async def test_chat_with_custom_max_tokens(self, test_app: FastAPI, mock_chat_service):
        """Test chat with custom max_tokens"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            await client.post(
                "/api/v1/chat",
                json={
                    "text": "Hello",
                    "user_id": 1,
                    "max_tokens": 100
                }
            )

            call_args = mock_chat_service.process_message.call_args
            assert call_args.kwargs["max_tokens"] == 100

    @pytest.mark.asyncio
    async def test_chat_response_includes_tokens_used(self, test_app: FastAPI, mock_chat_service):
        """Test that response includes tokens_used"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={"text": "Hello", "user_id": 1}
            )
            data = response.json()
            assert "tokens_used" in data

    @pytest.mark.asyncio
    async def test_chat_handles_service_error(self, test_app: FastAPI, mock_chat_service):
        """Test that chat endpoint handles service errors gracefully"""
        # Mock service to raise an error
        mock_chat_service.process_message.side_effect = Exception("Service error")

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={"text": "Hello", "user_id": 1}
            )
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_chat_validates_temperature_range(self, test_app: FastAPI):
        """Test that temperature must be between 0 and 2"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            # Test temperature > 2
            response = await client.post(
                "/api/v1/chat",
                json={
                    "text": "Hello",
                    "user_id": 1,
                    "temperature": 3.0
                }
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_validates_max_tokens_positive(self, test_app: FastAPI):
        """Test that max_tokens must be positive"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={
                    "text": "Hello",
                    "user_id": 1,
                    "max_tokens": -1
                }
            )
            assert response.status_code == 422
