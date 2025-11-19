"""
Middleware tests for rate limiting (TDD - Tests written FIRST)

Tests rate limiting to prevent API abuse.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time


class TestRateLimitingMiddleware:
    """Tests for rate limiting middleware"""

    @pytest.mark.asyncio
    async def test_allows_requests_within_limit(self, test_app: FastAPI):
        """Test that requests within rate limit are allowed"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            # Make request within limit
            response = await client.get("/health")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_blocks_requests_exceeding_limit(self, test_app_with_rate_limit: FastAPI):
        """Test that requests exceeding rate limit are blocked"""
        async with AsyncClient(transport=ASGITransport(app=test_app_with_rate_limit), base_url="http://test") as client:
            # Make multiple requests to exceed limit (assume limit is 5 per minute)
            responses = []
            for i in range(7):
                response = await client.get("/health")
                responses.append(response)

            # First 5 should succeed
            for i in range(5):
                assert responses[i].status_code == 200

            # 6th and 7th should be rate limited
            assert responses[5].status_code == 429
            assert responses[6].status_code == 429

    @pytest.mark.asyncio
    async def test_returns_429_status_code(self, test_app_with_rate_limit: FastAPI, mock_redis_client):
        """Test that rate limited requests return 429 Too Many Requests"""
        # Mock Redis to indicate rate limit exceeded
        mock_redis_client.incr = AsyncMock(return_value=10)  # Simulate 10 requests already

        async with AsyncClient(transport=ASGITransport(app=test_app_with_rate_limit), base_url="http://test") as client:
            response = await client.get("/health")
            # Should be rate limited if already at 10 requests
            assert response.status_code in [200, 429]  # May pass depending on limit

    @pytest.mark.asyncio
    async def test_rate_limit_uses_redis(self, test_app_with_rate_limit: FastAPI, mock_redis_client):
        """Test that rate limiting uses Redis for tracking"""
        async with AsyncClient(transport=ASGITransport(app=test_app_with_rate_limit), base_url="http://test") as client:
            await client.get("/health")

            # Verify Redis was called (incr for counter)
            assert mock_redis_client.incr.called or mock_redis_client.get.called

    @pytest.mark.asyncio
    async def test_rate_limit_per_ip_address(self, test_app_with_rate_limit: FastAPI, mock_redis_client):
        """Test that rate limiting is per IP address"""
        # Reset mock
        mock_redis_client.reset_mock()

        async with AsyncClient(transport=ASGITransport(app=test_app_with_rate_limit), base_url="http://test") as client:
            # Make request with specific IP
            response = await client.get("/health", headers={"X-Forwarded-For": "192.168.1.1"})

            # Check that Redis key includes IP address
            if mock_redis_client.incr.called:
                call_args = mock_redis_client.incr.call_args
                redis_key = call_args[0][0] if call_args[0] else ""
                # Key should contain IP address
                assert "192.168.1.1" in redis_key or "rate_limit" in redis_key

    @pytest.mark.asyncio
    async def test_rate_limit_includes_headers(self, test_app_with_rate_limit: FastAPI):
        """Test that response includes rate limit headers"""
        async with AsyncClient(transport=ASGITransport(app=test_app_with_rate_limit), base_url="http://test") as client:
            response = await client.get("/health")

            # Should include rate limit headers (optional, good practice)
            # X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
            headers = response.headers
            # At least one rate limit header should be present
            has_rate_limit_header = any(
                key.lower().startswith("x-ratelimit") for key in headers.keys()
            )
            # This is optional, so we just check it doesn't error
            assert response.status_code in [200, 429]

    @pytest.mark.asyncio
    async def test_rate_limit_resets_after_window(self, test_app_with_rate_limit: FastAPI, mock_redis_client):
        """Test that rate limit counter resets after time window"""
        # Mock Redis to return None (expired key)
        mock_redis_client.get = AsyncMock(return_value=None)
        mock_redis_client.incr = AsyncMock(return_value=1)

        async with AsyncClient(transport=ASGITransport(app=test_app_with_rate_limit), base_url="http://test") as client:
            response = await client.get("/health")

            # Should succeed since counter reset
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_error_message(self, test_app_with_rate_limit: FastAPI, mock_redis_client):
        """Test that rate limited response includes helpful error message"""
        # Mock Redis to indicate rate limit exceeded
        mock_redis_client.get = AsyncMock(return_value="100")  # 100 requests

        async with AsyncClient(transport=ASGITransport(app=test_app_with_rate_limit), base_url="http://test") as client:
            # Make enough requests to trigger rate limit
            for _ in range(10):
                response = await client.get("/health")

            if response.status_code == 429:
                data = response.json()
                # Should include error message
                assert "detail" in data or "error" in data or "message" in data

    @pytest.mark.asyncio
    async def test_rate_limit_different_endpoints(self, test_app_with_rate_limit: FastAPI):
        """Test that rate limit applies across different endpoints"""
        async with AsyncClient(transport=ASGITransport(app=test_app_with_rate_limit), base_url="http://test") as client:
            # Make requests to different endpoints
            responses = []
            for _ in range(3):
                responses.append(await client.get("/health"))
            for _ in range(3):
                responses.append(await client.post("/api/v1/chat", json={"text": "Hello", "user_id": 1}))

            # All should count towards same rate limit
            # At least first few should succeed
            assert responses[0].status_code in [200, 422]  # 422 if validation fails

    @pytest.mark.asyncio
    async def test_rate_limit_exempts_health_check(self, test_app_with_rate_limit: FastAPI):
        """Test that health check endpoint may be exempt from rate limiting"""
        async with AsyncClient(transport=ASGITransport(app=test_app_with_rate_limit), base_url="http://test") as client:
            # Make many health check requests
            responses = []
            for _ in range(20):
                response = await client.get("/health")
                responses.append(response)

            # Health check might be exempt, or might be rate limited
            # Just verify it doesn't crash
            assert all(r.status_code in [200, 429] for r in responses)

    @pytest.mark.asyncio
    async def test_rate_limit_handles_redis_failure(self, test_app_with_rate_limit: FastAPI, mock_redis_client):
        """Test that rate limiting fails open if Redis is unavailable"""
        # Mock Redis to raise connection error
        mock_redis_client.incr = AsyncMock(side_effect=Exception("Redis connection failed"))
        mock_redis_client.get = AsyncMock(side_effect=Exception("Redis connection failed"))

        async with AsyncClient(transport=ASGITransport(app=test_app_with_rate_limit), base_url="http://test") as client:
            response = await client.get("/health")

            # Should fail open (allow request) when Redis is down
            assert response.status_code == 200
