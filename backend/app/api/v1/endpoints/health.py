"""
Health check endpoints

Provides system health monitoring, dependency checks, and readiness probes.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict
from datetime import datetime, timezone
import logging

from app.core.config import get_settings
from app.api.deps import get_db_session, get_redis_client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from redis.asyncio import Redis

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str  # healthy, degraded, unhealthy
    app: str
    version: str
    timestamp: str
    checks: Dict[str, str]  # service_name: status (ok/error)


class ReadinessResponse(BaseModel):
    """Readiness probe response"""
    ready: bool
    checks: Dict[str, str]


@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),
):
    """
    Health check endpoint.

    Checks the status of all critical dependencies:
    - Database connection
    - Redis cache connection

    Returns:
        HealthResponse with overall status and individual check results

    Status levels:
        - healthy: All checks pass
        - degraded: Some non-critical checks fail
        - unhealthy: Critical checks fail
    """
    checks = {}

    # Check database connection
    try:
        # Execute simple query to verify connection
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
        logger.debug("Database health check: OK")
    except Exception as e:
        checks["database"] = "error"
        logger.error(f"Database health check failed: {e}")

    # Check Redis connection
    try:
        await redis.ping()
        checks["redis"] = "ok"
        logger.debug("Redis health check: OK")
    except Exception as e:
        checks["redis"] = "error"
        logger.error(f"Redis health check failed: {e}")

    # Determine overall status
    failed_checks = [k for k, v in checks.items() if v == "error"]

    if not failed_checks:
        overall_status = "healthy"
    elif "database" in failed_checks:
        # Database is critical
        overall_status = "unhealthy"
    else:
        # Only Redis failed (can operate without cache)
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        checks=checks,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),
):
    """
    Readiness probe endpoint.

    Used by container orchestration (Kubernetes) to determine if the
    application is ready to accept traffic.

    Returns:
        200 if ready, 503 if not ready
    """
    checks = {}
    ready = True

    # Check database (critical for readiness)
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = "error"
        ready = False
        logger.error(f"Readiness check - database failed: {e}")

    # Check Redis (optional for readiness)
    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = "error"
        logger.warning(f"Readiness check - redis failed: {e}")
        # Don't mark as not ready for Redis failure

    return ReadinessResponse(
        ready=ready,
        checks=checks,
    )
