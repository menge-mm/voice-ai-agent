"""
Unit tests for Redis Cache service (TDD - Tests written FIRST)

CacheService will:
- Wrap async Redis operations
- Cache OpenAI responses by conversation context
- Cache TTS audio by text hash
- Implement TTL (time-to-live)
- Handle cache misses gracefully
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.cache.cache_service import CacheService, CacheMiss
import json
import hashlib


class TestCacheService:
    """Test suite for CacheService"""

    @pytest.fixture
    def mock_redis(self):
        """Mock async Redis client"""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.set = AsyncMock(return_value=True)
        redis.delete = AsyncMock(return_value=1)
        redis.flushdb = AsyncMock(return_value=True)
        redis.ping = AsyncMock(return_value=True)
        redis.close = AsyncMock()
        return redis

    @pytest.fixture
    def cache_service(self, mock_redis):
        """Create CacheService with mocked Redis"""
        return CacheService(redis_client=mock_redis, default_ttl=3600)

    async def test_get_returns_cached_value(self, cache_service, mock_redis):
        """Test retrieving a cached value"""
        mock_redis.get.return_value = b'"cached_value"'

        value = await cache_service.get("test_key")

        assert value == "cached_value"
        mock_redis.get.assert_called_once_with("test_key")

    async def test_get_raises_cache_miss_when_not_found(self, cache_service, mock_redis):
        """Test that CacheMiss is raised when key doesn't exist"""
        mock_redis.get.return_value = None

        with pytest.raises(CacheMiss):
            await cache_service.get("missing_key")

    async def test_get_with_default_returns_default_on_miss(self, cache_service, mock_redis):
        """Test get with default value on cache miss"""
        mock_redis.get.return_value = None

        value = await cache_service.get("missing_key", default="default_value")

        assert value == "default_value"

    async def test_set_stores_value_with_ttl(self, cache_service, mock_redis):
        """Test storing a value with TTL"""
        await cache_service.set("test_key", "test_value", ttl=1800)

        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args.args[0] == "test_key"
        assert json.loads(call_args.args[1]) == "test_value"
        assert call_args.kwargs["ex"] == 1800

    async def test_set_uses_default_ttl_when_not_specified(self, cache_service, mock_redis):
        """Test that default TTL is used when not specified"""
        await cache_service.set("test_key", "test_value")

        call_args = mock_redis.set.call_args
        assert call_args.kwargs["ex"] == 3600  # default_ttl

    async def test_set_supports_complex_objects(self, cache_service, mock_redis):
        """Test storing complex objects (dicts, lists)"""
        complex_value = {"key": "value", "nested": {"data": [1, 2, 3]}}

        await cache_service.set("complex_key", complex_value)

        call_args = mock_redis.set.call_args
        stored_value = json.loads(call_args.args[1])
        assert stored_value == complex_value

    async def test_delete_removes_key(self, cache_service, mock_redis):
        """Test deleting a cached key"""
        mock_redis.delete.return_value = 1

        result = await cache_service.delete("test_key")

        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")

    async def test_delete_returns_false_when_key_not_found(self, cache_service, mock_redis):
        """Test delete returns False when key doesn't exist"""
        mock_redis.delete.return_value = 0

        result = await cache_service.delete("missing_key")

        assert result is False

    async def test_clear_flushes_database(self, cache_service, mock_redis):
        """Test clearing all cache entries"""
        await cache_service.clear()

        mock_redis.flushdb.assert_called_once()

    async def test_ping_checks_connection(self, cache_service, mock_redis):
        """Test ping checks Redis connection"""
        is_connected = await cache_service.ping()

        assert is_connected is True
        mock_redis.ping.assert_called_once()

    async def test_ping_returns_false_on_error(self, cache_service, mock_redis):
        """Test ping returns False when Redis is unavailable"""
        mock_redis.ping.side_effect = Exception("Connection failed")

        is_connected = await cache_service.ping()

        assert is_connected is False

    async def test_cache_openai_response(self, cache_service, mock_redis):
        """Test caching OpenAI response with conversation context"""
        await cache_service.cache_openai_response(
            conversation_id="conv-123",
            user_message="Hello",
            ai_response="Hi there!",
            ttl=7200
        )

        # Should generate consistent cache key
        call_args = mock_redis.set.call_args
        cache_key = call_args.args[0]
        assert "openai" in cache_key
        assert ":" in cache_key  # Should have format "openai:hash"

        # Should store the AI response
        stored_data = json.loads(call_args.args[1])
        assert stored_data["response"] == "Hi there!"
        assert stored_data["user_message"] == "Hello"

    async def test_get_cached_openai_response(self, cache_service, mock_redis):
        """Test retrieving cached OpenAI response"""
        cached_data = {
            "response": "Cached AI response",
            "user_message": "Test message"
        }
        mock_redis.get.return_value = json.dumps(cached_data).encode()

        result = await cache_service.get_cached_openai_response(
            conversation_id="conv-123",
            user_message="Test message"
        )

        assert result == "Cached AI response"

    async def test_get_cached_openai_response_returns_none_on_miss(
        self,
        cache_service,
        mock_redis
    ):
        """Test that None is returned when OpenAI cache misses"""
        mock_redis.get.return_value = None

        result = await cache_service.get_cached_openai_response(
            conversation_id="conv-123",
            user_message="Test"
        )

        assert result is None

    async def test_cache_tts_audio(self, cache_service, mock_redis):
        """Test caching TTS audio with text hash"""
        audio_bytes = b"fake audio data"

        await cache_service.cache_tts_audio(
            text="Hello world",
            language="en",
            audio_bytes=audio_bytes
        )

        call_args = mock_redis.set.call_args
        cache_key = call_args.args[0]

        # Should use hash of text+language for key
        assert "tts" in cache_key

        # Should store the audio bytes (base64 encoded)
        stored_data = json.loads(call_args.args[1])
        assert "audio" in stored_data

    async def test_get_cached_tts_audio(self, cache_service, mock_redis):
        """Test retrieving cached TTS audio"""
        import base64
        audio_bytes = b"fake audio data"
        cached_data = {
            "audio": base64.b64encode(audio_bytes).decode(),
            "text": "Hello world"
        }
        mock_redis.get.return_value = json.dumps(cached_data).encode()

        result = await cache_service.get_cached_tts_audio(
            text="Hello world",
            language="en"
        )

        assert result == audio_bytes

    async def test_get_cached_tts_audio_returns_none_on_miss(
        self,
        cache_service,
        mock_redis
    ):
        """Test that None is returned when TTS cache misses"""
        mock_redis.get.return_value = None

        result = await cache_service.get_cached_tts_audio(
            text="Test",
            language="en"
        )

        assert result is None

    async def test_generate_cache_key_is_consistent(self, cache_service):
        """Test that cache key generation is deterministic"""
        key1 = cache_service.generate_cache_key("prefix", "data1", "data2")
        key2 = cache_service.generate_cache_key("prefix", "data1", "data2")

        assert key1 == key2

    async def test_generate_cache_key_differs_for_different_inputs(self, cache_service):
        """Test that different inputs generate different cache keys"""
        key1 = cache_service.generate_cache_key("prefix", "data1")
        key2 = cache_service.generate_cache_key("prefix", "data2")

        assert key1 != key2

    async def test_close_closes_redis_connection(self, cache_service, mock_redis):
        """Test that close() closes the Redis connection"""
        await cache_service.close()

        mock_redis.close.assert_called_once()

    async def test_context_manager_support(self, mock_redis):
        """Test using CacheService as async context manager"""
        async with CacheService(redis_client=mock_redis) as cache:
            await cache.set("test", "value")

        # Should close on exit
        mock_redis.close.assert_called_once()
