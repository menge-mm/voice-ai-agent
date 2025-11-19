"""
Redis Cache Service for caching OpenAI responses and TTS audio

Provides async Redis operations with convenience methods for
caching AI completions and synthesized audio.
"""

import json
import hashlib
import base64
import logging
from typing import Any, Optional
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class CacheMiss(Exception):
    """Raised when a requested cache key is not found"""
    pass


class CacheService:
    """
    Async Redis cache service.

    Provides caching for:
    - OpenAI completions (by conversation context)
    - TTS audio (by text hash)
    - Generic key-value storage

    Example:
        ```python
        async with CacheService(redis_client) as cache:
            # Cache OpenAI response
            await cache.cache_openai_response(
                conversation_id="conv-123",
                user_message="Hello",
                ai_response="Hi there!"
            )

            # Retrieve cached response
            response = await cache.get_cached_openai_response(
                conversation_id="conv-123",
                user_message="Hello"
            )
        ```
    """

    def __init__(
        self,
        redis_client: Redis,
        default_ttl: int = 3600
    ):
        """
        Initialize cache service.

        Args:
            redis_client: Async Redis client instance
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self.redis = redis_client
        self.default_ttl = default_ttl

    async def get(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found (optional)

        Returns:
            Cached value (deserialized from JSON)

        Raises:
            CacheMiss: If key not found and no default provided
        """
        try:
            value = await self.redis.get(key)

            if value is None:
                if default is not None:
                    return default
                raise CacheMiss(f"Cache key not found: {key}")

            # Deserialize from JSON
            return json.loads(value)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize cache value for key {key}: {e}")
            raise

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (uses default_ttl if None)

        Returns:
            True if successful
        """
        try:
            # Serialize to JSON
            serialized = json.dumps(value)

            # Use default TTL if not specified
            ttl = ttl if ttl is not None else self.default_ttl

            # Store in Redis
            await self.redis.set(key, serialized, ex=ttl)

            return True

        except Exception as e:
            logger.error(f"Failed to cache value for key {key}: {e}")
            raise

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False if key didn't exist
        """
        result = await self.redis.delete(key)
        return result > 0

    async def clear(self) -> None:
        """Clear all keys from the cache database"""
        await self.redis.flushdb()
        logger.info("✓ Cache cleared")

    async def ping(self) -> bool:
        """
        Check if Redis connection is alive.

        Returns:
            True if connected, False otherwise
        """
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    def generate_cache_key(self, prefix: str, *parts: str) -> str:
        """
        Generate a consistent cache key from components.

        Args:
            prefix: Key prefix (e.g., "openai", "tts")
            *parts: Additional parts to include in hash

        Returns:
            Cache key in format: prefix:hash
        """
        # Combine all parts
        combined = ":".join(str(part) for part in parts)

        # Generate hash
        hash_obj = hashlib.sha256(combined.encode())
        hash_str = hash_obj.hexdigest()[:16]  # Use first 16 chars

        return f"{prefix}:{hash_str}"

    async def cache_openai_response(
        self,
        conversation_id: str,
        user_message: str,
        ai_response: str,
        ttl: Optional[int] = None
    ) -> None:
        """
        Cache an OpenAI completion response.

        Args:
            conversation_id: ID of the conversation
            user_message: User's message
            ai_response: AI's response
            ttl: Time-to-live in seconds (optional)
        """
        # Generate cache key from conversation + message
        cache_key = self.generate_cache_key(
            "openai",
            conversation_id,
            user_message
        )

        # Store response with metadata
        cache_data = {
            "response": ai_response,
            "user_message": user_message,
            "conversation_id": conversation_id
        }

        await self.set(cache_key, cache_data, ttl=ttl)
        logger.info(f"✓ Cached OpenAI response for conversation {conversation_id}")

    async def get_cached_openai_response(
        self,
        conversation_id: str,
        user_message: str
    ) -> Optional[str]:
        """
        Retrieve cached OpenAI response.

        Args:
            conversation_id: ID of the conversation
            user_message: User's message

        Returns:
            Cached AI response, or None if not found
        """
        cache_key = self.generate_cache_key(
            "openai",
            conversation_id,
            user_message
        )

        try:
            cache_data = await self.get(cache_key)
            logger.info(f"✓ Cache hit for OpenAI response")
            return cache_data["response"]
        except CacheMiss:
            logger.debug(f"Cache miss for OpenAI response")
            return None

    async def cache_tts_audio(
        self,
        text: str,
        language: str,
        audio_bytes: bytes,
        ttl: Optional[int] = None
    ) -> None:
        """
        Cache TTS audio.

        Args:
            text: Text that was synthesized
            language: Language code
            audio_bytes: Audio data (WAV format)
            ttl: Time-to-live in seconds (optional)
        """
        # Generate cache key from text + language
        cache_key = self.generate_cache_key("tts", text, language)

        # Store audio (base64 encoded for JSON)
        cache_data = {
            "audio": base64.b64encode(audio_bytes).decode(),
            "text": text,
            "language": language
        }

        await self.set(cache_key, cache_data, ttl=ttl)
        logger.info(f"✓ Cached TTS audio for text: {text[:50]}...")

    async def get_cached_tts_audio(
        self,
        text: str,
        language: str
    ) -> Optional[bytes]:
        """
        Retrieve cached TTS audio.

        Args:
            text: Text to synthesize
            language: Language code

        Returns:
            Cached audio bytes, or None if not found
        """
        cache_key = self.generate_cache_key("tts", text, language)

        try:
            cache_data = await self.get(cache_key)
            logger.info(f"✓ Cache hit for TTS audio")
            # Decode base64 back to bytes
            return base64.b64decode(cache_data["audio"])
        except CacheMiss:
            logger.debug(f"Cache miss for TTS audio")
            return None

    async def close(self) -> None:
        """Close Redis connection"""
        await self.redis.close()
        logger.info("✓ Cache connection closed")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
