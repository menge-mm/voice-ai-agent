"""
Fixtures for API integration tests
"""

import pytest
import os
from fastapi import FastAPI
from unittest.mock import AsyncMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

# Set environment variables at module level BEFORE any imports
# This ensures they're set before Settings is first created
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test_db"
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:8080"


@pytest.fixture
def test_app(mock_db_session, mock_redis_client, mock_chat_service, mock_tts_service) -> FastAPI:
    """
    Create a FastAPI test application with mocked dependencies.

    This fixture provides a clean app instance for each test.
    Dependencies are overridden to avoid actual database/Redis connections.
    """
    from app.main import app
    from app.api.deps import get_db_session, get_redis_client, get_chat_service, get_tts_service

    # Override dependencies with mocks
    async def override_get_db():
        yield mock_db_session

    async def override_get_redis():
        yield mock_redis_client

    async def override_get_chat():
        yield mock_chat_service

    def override_get_tts():
        return mock_tts_service

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_redis_client] = override_get_redis
    app.dependency_overrides[get_chat_service] = override_get_chat
    app.dependency_overrides[get_tts_service] = override_get_tts

    yield app

    # Cleanup overrides
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db_session():
    """Mock database session for API tests"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock(return_value=Mock())  # Mock SQL execute
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for API tests"""
    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.aclose = AsyncMock()
    return redis


@pytest.fixture
def mock_openai_service():
    """Mock OpenAI service for API tests"""
    service = Mock()
    service.get_completion = AsyncMock(return_value="Hello! How can I help you?")
    service.get_completion_with_tokens = AsyncMock(
        return_value=("Hello! How can I help you?", 25)
    )
    return service


@pytest.fixture
def mock_tts_service():
    """Mock TTS service for API tests"""
    service = Mock()
    service.synthesize = AsyncMock(return_value=b"fake_audio_bytes")
    service.is_loaded = True
    return service


@pytest.fixture
def mock_chat_service():
    """Mock Chat service for API tests"""
    from app.services.chat_service import ChatResponse

    service = Mock()
    service.process_message = AsyncMock(
        return_value=ChatResponse(
            text="Hello! How can I help you?",
            conversation_id="test-conv-123",
            audio=b"fake_audio_bytes",
            tokens_used=25,
        )
    )
    return service
