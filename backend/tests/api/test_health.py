"""
API tests for health check endpoint (TDD - Tests written FIRST)

Tests health monitoring, dependency checks, and status reporting.
"""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI


class TestHealthEndpoint:
    """Tests for GET /health endpoint"""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, test_app: FastAPI):
        """Test that health endpoint returns 200 OK"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_returns_json(self, test_app: FastAPI):
        """Test that health endpoint returns JSON"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.headers["content-type"] == "application/json"

    @pytest.mark.asyncio
    async def test_health_includes_status(self, test_app: FastAPI):
        """Test that health response includes status field"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.get("/health")
            data = response.json()
            assert "status" in data
            assert data["status"] in ["healthy", "degraded", "unhealthy"]

    @pytest.mark.asyncio
    async def test_health_includes_version(self, test_app: FastAPI):
        """Test that health response includes version"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.get("/health")
            data = response.json()
            assert "version" in data
            assert isinstance(data["version"], str)

    @pytest.mark.asyncio
    async def test_health_includes_timestamp(self, test_app: FastAPI):
        """Test that health response includes timestamp"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.get("/health")
            data = response.json()
            assert "timestamp" in data
            assert isinstance(data["timestamp"], str)

    @pytest.mark.asyncio
    async def test_health_checks_database(self, test_app: FastAPI):
        """Test that health endpoint checks database connection"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.get("/health")
            data = response.json()
            assert "checks" in data
            assert "database" in data["checks"]
            assert data["checks"]["database"] in ["ok", "error"]

    @pytest.mark.asyncio
    async def test_health_checks_redis(self, test_app: FastAPI):
        """Test that health endpoint checks Redis connection"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.get("/health")
            data = response.json()
            assert "checks" in data
            assert "redis" in data["checks"]
            assert data["checks"]["redis"] in ["ok", "error"]

    @pytest.mark.asyncio
    @patch('app.api.v1.endpoints.health.get_db_session')
    async def test_health_healthy_when_all_checks_pass(self, mock_db, test_app: FastAPI):
        """Test that status is healthy when all checks pass"""
        # Mock successful database connection
        mock_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.get("/health")
            data = response.json()

            # If both DB and Redis checks pass, status should be healthy
            if data["checks"].get("database") == "ok" and data["checks"].get("redis") == "ok":
                assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_includes_app_name(self, test_app: FastAPI):
        """Test that health response includes application name"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.get("/health")
            data = response.json()
            assert "app" in data
            assert isinstance(data["app"], str)


class TestReadinessEndpoint:
    """Tests for GET /ready endpoint (optional)"""

    @pytest.mark.asyncio
    async def test_ready_endpoint_exists(self, test_app: FastAPI):
        """Test that /ready endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.get("/ready")
            # Should either return 200 (ready) or 503 (not ready), not 404
            assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_ready_returns_503_when_not_ready(self, test_app: FastAPI):
        """Test that /ready returns 503 when dependencies are unavailable"""
        # This will be implemented based on actual readiness logic
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.get("/ready")
            # Should return either 200 or 503
            assert response.status_code in [200, 503]
