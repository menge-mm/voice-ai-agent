"""
API Dependency Injection

Provides FastAPI dependencies for:
- Database sessions
- Redis clients
- Service instances (OpenAI, TTS, Cache, Chat)

All dependencies use proper lifecycle management with async generators.
"""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from openai import AsyncOpenAI

from app.db.session import async_session
from app.core.config import get_settings
from app.cache.cache_service import CacheService
from app.services.openai_service import OpenAIService
from app.services.tts_service import TTSService
from app.services.chat_service import ChatService
from app.repositories.conversation_repo import ConversationRepository

settings = get_settings()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for database session.

    Yields:
        AsyncSession: Database session that automatically closes after use

    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db_session)):
            return await user_repo.get_all()
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """
    Dependency for Redis client.

    Yields:
        Redis: Redis client that automatically closes after use

    Example:
        @app.get("/cache-stats")
        async def cache_stats(redis: Redis = Depends(get_redis_client)):
            return await redis.info()
    """
    redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=False,  # Handle binary data
    )
    try:
        yield redis
    finally:
        await redis.aclose()


async def get_openai_client() -> AsyncOpenAI:
    """
    Dependency for OpenAI client.

    Returns:
        AsyncOpenAI: OpenAI client configured with API key

    Note:
        This is not a generator because AsyncOpenAI handles
        connection pooling internally and doesn't need explicit cleanup.

    Example:
        @app.post("/completions")
        async def complete(client: AsyncOpenAI = Depends(get_openai_client)):
            return await client.chat.completions.create(...)
    """
    api_key = os.getenv("OPENAI_API_KEY", settings.OPENAI_API_KEY)
    return AsyncOpenAI(api_key=api_key)


async def get_cache_service(
    redis: Redis = None,
) -> AsyncGenerator[CacheService, None]:
    """
    Dependency for CacheService.

    Args:
        redis: Redis client (auto-injected by FastAPI)

    Yields:
        CacheService: Cache service that automatically closes after use

    Example:
        @app.get("/cache/{key}")
        async def get_cached(
            key: str,
            cache: CacheService = Depends(get_cache_service)
        ):
            return await cache.get(key)
    """
    # Create Redis client if not provided (for testing)
    if redis is None:
        redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=False,
        )
        should_close_redis = True
    else:
        should_close_redis = False

    cache = CacheService(
        redis_client=redis,
        default_ttl=settings.CACHE_TTL,
    )

    try:
        yield cache
    finally:
        if should_close_redis:
            await redis.aclose()


async def get_openai_service() -> AsyncGenerator[OpenAIService, None]:
    """
    Dependency for OpenAIService.

    Yields:
        OpenAIService: OpenAI service with conversation history support

    Example:
        @app.post("/chat")
        async def chat(
            message: str,
            openai: OpenAIService = Depends(get_openai_service)
        ):
            return await openai.get_completion(message)
    """
    # Create session and dependencies
    async with async_session() as db:
        try:
            openai_client = await get_openai_client()

            # Create repository and service
            conversation_repo = ConversationRepository(db)
            service = OpenAIService(
                openai_client=openai_client,
                conversation_repo=conversation_repo,
                model=settings.OPENAI_MODEL,
            )

            yield service
        finally:
            await db.close()


async def get_tts_service() -> TTSService:
    """
    Dependency for TTSService.

    Returns:
        TTSService: TTS service (singleton-like, models loaded on demand)

    Note:
        TTSService is returned directly (not yielded) because:
        - Models are loaded lazily on first use
        - Model unloading is manual via unload_model()
        - We don't want to unload models after each request

    Example:
        @app.post("/tts")
        async def synthesize(
            text: str,
            tts: TTSService = Depends(get_tts_service)
        ):
            audio = await tts.synthesize(text)
            return audio
    """
    return TTSService(
        model_name=settings.TTS_MODEL,
        force_cpu=settings.TTS_FORCE_CPU,
    )


async def get_chat_service() -> AsyncGenerator[ChatService, None]:
    """
    Dependency for ChatService (orchestration layer).

    Yields:
        ChatService: Chat service that orchestrates OpenAI + TTS + DB

    Example:
        @app.post("/chat")
        async def chat(
            request: ChatRequest,
            chat: ChatService = Depends(get_chat_service)
        ):
            response = await chat.process_message(
                text=request.text,
                user_id=request.user_id,
                generate_audio=request.with_audio,
            )
            return response.to_dict()
    """
    # Create session and dependencies
    async with async_session() as db:
        try:
            # Create OpenAI client
            openai_client = await get_openai_client()

            # Get TTS service
            tts_service = await get_tts_service()

            # Create repositories and services
            conversation_repo = ConversationRepository(db)
            openai_service = OpenAIService(
                openai_client=openai_client,
                conversation_repo=conversation_repo,
                model=settings.OPENAI_MODEL,
            )

            chat_service = ChatService(
                openai_service=openai_service,
                tts_service=tts_service,
                conversation_repo=conversation_repo,
            )

            yield chat_service
        finally:
            await db.close()
