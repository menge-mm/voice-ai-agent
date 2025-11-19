"""
Rate limiting middleware

Prevents API abuse by limiting requests per IP address.
"""

import logging
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from redis.asyncio import Redis
import time

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis for distributed rate limiting.

    Tracks requests per IP address and blocks requests exceeding the limit.
    """

    def __init__(
        self,
        app,
        redis_client: Redis,
        max_requests: int = 100,
        window_seconds: int = 60,
        exempt_paths: list[str] = None,
    ):
        """
        Initialize rate limiting middleware.

        Args:
            app: FastAPI application
            redis_client: Redis client for tracking requests
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
            exempt_paths: List of paths exempt from rate limiting (e.g., ["/health"])
        """
        super().__init__(app)
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.exempt_paths = exempt_paths or []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response or 429 Too Many Requests if rate limited
        """
        # Check if path is exempt from rate limiting
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Get client IP address
        client_ip = self._get_client_ip(request)

        # Generate Redis key for rate limiting
        rate_limit_key = f"rate_limit:{client_ip}:{int(time.time() / self.window_seconds)}"

        try:
            # Increment request counter
            request_count = await self.redis.incr(rate_limit_key)

            # Set expiration on first request in window
            if request_count == 1:
                await self.redis.expire(rate_limit_key, self.window_seconds)

            # Check if rate limit exceeded
            if request_count > self.max_requests:
                logger.warning(
                    f"Rate limit exceeded for IP {client_ip}: "
                    f"{request_count}/{self.max_requests} requests"
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Rate limit exceeded. Maximum {self.max_requests} requests "
                        f"per {self.window_seconds} seconds allowed."
                    },
                    headers={
                        "X-RateLimit-Limit": str(self.max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(self.window_seconds),
                    },
                )

            # Process request
            response = await call_next(request)

            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(self.max_requests)
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, self.max_requests - request_count)
            )
            response.headers["X-RateLimit-Reset"] = str(self.window_seconds)

            return response

        except Exception as e:
            # Fail open: if Redis is down, allow request
            logger.error(f"Rate limiting error: {e}", exc_info=True)
            logger.warning("Rate limiting disabled due to Redis error - failing open")
            return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.

        Args:
            request: Incoming request

        Returns:
            Client IP address
        """
        # Check X-Forwarded-For header (for proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, use first one
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to client host
        if request.client:
            return request.client.host

        # Default fallback
        return "unknown"
