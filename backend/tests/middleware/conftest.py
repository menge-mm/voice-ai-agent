"""
Fixtures for middleware tests
"""

import pytest
import os
from fastapi import FastAPI
from unittest.mock import AsyncMock, Mock
from redis.asyncio import Redis

# Set environment variables at module level BEFORE any imports
# This ensures they're set before Settings is first created
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test_db"
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:8080"


@pytest.fixture
def test_app_with_rate_limit(mock_db_session, mock_redis_client, mock_chat_service, mock_tts_service) -> FastAPI:
    """
    Create a fresh FastAPI test application with rate limiting middleware enabled.

    This fixture creates a NEW app instance (not the imported one) to avoid
    the "Cannot add middleware after an application has started" error.
    """
    from app.api.deps import get_db_session, get_redis_client, get_chat_service, get_tts_service
    from app.middleware.rate_limiting import RateLimitMiddleware
    from app.api.v1.endpoints import health, chat, tts
    from app.core.config import get_settings

    settings = get_settings()

    # Create a fresh app instance
    fresh_app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
    )

    # Add middleware BEFORE adding routes
    fresh_app.add_middleware(
        RateLimitMiddleware,
        redis_client=mock_redis_client,
        max_requests=5,
        window_seconds=60,
    )

    # Add routes
    fresh_app.include_router(health.router, prefix="", tags=["Health"])
    fresh_app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
    fresh_app.include_router(tts.router, prefix="/api/v1", tags=["TTS"])

    # Override dependencies with mocks
    async def override_get_db():
        yield mock_db_session

    async def override_get_redis():
        yield mock_redis_client

    async def override_get_chat():
        yield mock_chat_service

    def override_get_tts():
        return mock_tts_service

    fresh_app.dependency_overrides[get_db_session] = override_get_db
    fresh_app.dependency_overrides[get_redis_client] = override_get_redis
    fresh_app.dependency_overrides[get_chat_service] = override_get_chat
    fresh_app.dependency_overrides[get_tts_service] = override_get_tts

    yield fresh_app

    # Cleanup overrides
    fresh_app.dependency_overrides.clear()


@pytest.fixture
def mock_redis_client_with_rate_limit():
    """Mock Redis client with rate limiting behavior"""
    redis = AsyncMock(spec=Redis)
    redis.ping = AsyncMock(return_value=True)

    # Mock rate limit counter
    request_count = {"value": 0}

    async def mock_incr(key):
        request_count["value"] += 1
        return request_count["value"]

    async def mock_get(key):
        return str(request_count["value"]) if request_count["value"] > 0 else None

    async def mock_setex(key, seconds, value):
        return True

    async def mock_expire(key, seconds):
        return True

    redis.incr = AsyncMock(side_effect=mock_incr)
    redis.get = AsyncMock(side_effect=mock_get)
    redis.setex = AsyncMock(side_effect=mock_setex)
    redis.expire = AsyncMock(side_effect=mock_expire)
    redis.delete = AsyncMock(return_value=1)
    redis.aclose = AsyncMock()

    return redis


@pytest.fixture
def test_app_with_logging(mock_db_session, mock_redis_client, mock_chat_service, mock_tts_service) -> FastAPI:
    """
    Create a fresh FastAPI test application with logging middleware enabled.
    """
    from app.api.deps import get_db_session, get_redis_client, get_chat_service, get_tts_service
    from app.middleware.logging import RequestLoggingMiddleware
    from app.api.v1.endpoints import health, chat, tts
    from app.core.config import get_settings

    settings = get_settings()

    # Create a fresh app instance
    fresh_app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
    )

    # Add logging middleware BEFORE adding routes
    fresh_app.add_middleware(RequestLoggingMiddleware)

    # Add routes
    fresh_app.include_router(health.router, prefix="", tags=["Health"])
    fresh_app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
    fresh_app.include_router(tts.router, prefix="/api/v1", tags=["TTS"])

    # Override dependencies with mocks
    async def override_get_db():
        yield mock_db_session

    async def override_get_redis():
        yield mock_redis_client

    async def override_get_chat():
        yield mock_chat_service

    def override_get_tts():
        return mock_tts_service

    fresh_app.dependency_overrides[get_db_session] = override_get_db
    fresh_app.dependency_overrides[get_redis_client] = override_get_redis
    fresh_app.dependency_overrides[get_chat_service] = override_get_chat
    fresh_app.dependency_overrides[get_tts_service] = override_get_tts

    yield fresh_app

    # Cleanup overrides
    fresh_app.dependency_overrides.clear()
