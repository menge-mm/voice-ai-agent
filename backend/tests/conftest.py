"""
Pytest configuration and shared fixtures
"""
import os

# IMPORTANT: Set environment variables BEFORE any app imports
# This ensures Settings validation passes when modules are imported
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")  # Use SQLite for unit test fixtures
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-for-testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-production")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")

import pytest
from typing import AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import text

# Mock the database engine creation at module level to prevent connection attempts
# when deps.py or session.py are imported during test collection
mock_engine = AsyncMock()
mock_engine.begin = AsyncMock()
mock_engine.dispose = AsyncMock()

# Import Base and all models at module level so they're registered
from app.db.base import Base
from app.db.models.user import User
from app.db.models.conversation import Conversation
from app.db.models.message import Message


@pytest.fixture(autouse=True, scope="function")
def clear_settings_cache():
    """
    Clear settings and database caches before each test function.

    This prevents cache pollution when running multiple test suites together.
    The @lru_cache() decorators create singletons that can conflict when
    different test suites modify environment variables.
    """
    from app.core.config import get_settings
    from app.db.session import get_engine, get_async_session

    # Clear all caches before each test
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_async_session.cache_clear()

    yield

    # Clear all caches after each test
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_async_session.cache_clear()


@pytest.fixture
def clean_env(monkeypatch):
    """Fixture to provide a clean environment for testing"""
    # Store original env
    original_env = os.environ.copy()

    yield monkeypatch

    # Restore original env
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="function")
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an async database session for testing.
    Uses in-memory SQLite for fast tests.

    Important: For SQLite :memory: databases, we must use a single connection
    throughout the test, otherwise each new connection gets a fresh empty database.
    """
    # Create in-memory SQLite database for testing
    # StaticPool ensures all connections use the same in-memory database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Provide session for test
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    # Cleanup
    await engine.dispose()


# ============================================================================
# Mock fixtures for API and middleware tests
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Mock database session for API/middleware tests"""
    from sqlalchemy.ext.asyncio import AsyncSession

    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock(return_value=Mock())  # Mock SQL execute
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for API/middleware tests with stateful rate limiting"""
    from redis.asyncio import Redis

    redis = AsyncMock(spec=Redis)
    redis.ping = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.setex = AsyncMock(return_value=True)
    redis.aclose = AsyncMock()

    # Make incr() and expire() stateful for rate limiting tests
    request_counters = {}

    async def mock_incr(key):
        """Increment counter for key"""
        if key not in request_counters:
            request_counters[key] = 0
        request_counters[key] += 1
        return request_counters[key]

    async def mock_expire(key, seconds):
        """Mock expire operation"""
        return True

    redis.incr = AsyncMock(side_effect=mock_incr)
    redis.expire = AsyncMock(side_effect=mock_expire)

    return redis


@pytest.fixture
def mock_openai_service():
    """Mock OpenAI service for API/middleware tests"""
    service = Mock()
    service.get_completion = AsyncMock(return_value="Hello! How can I help you?")
    service.get_completion_with_tokens = AsyncMock(
        return_value=("Hello! How can I help you?", 25)
    )
    return service


@pytest.fixture
def mock_tts_service():
    """Mock TTS service for API/middleware tests"""
    service = Mock()
    service.synthesize = AsyncMock(return_value=b"fake_audio_bytes")
    service.is_loaded = True
    return service


@pytest.fixture
def mock_chat_service():
    """Mock Chat service for API/middleware tests"""
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


@pytest.fixture
def test_app(mock_db_session, mock_redis_client, mock_chat_service, mock_tts_service):
    """
    Create a FastAPI test application with mocked dependencies (NO middleware).

    This fixture provides a clean app instance for each test.
    Dependencies are overridden to avoid actual database/Redis connections.
    """
    from fastapi import FastAPI
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
