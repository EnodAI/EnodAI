"""
Redis-based rate limiting middleware
"""
import time
from typing import Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
from loguru import logger
from app.config import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis
    Implements sliding window algorithm
    """

    def __init__(self, app, redis_client: redis.Redis = None):
        super().__init__(app)
        self.redis_client = redis_client
        self.settings = get_settings()

        # Rate limit configuration
        self.rate_limits = {
            "/api/v1/metrics": {"requests": 100, "window": 60},  # 100 req/min
            "/api/v1/alerts": {"requests": 50, "window": 60},    # 50 req/min
            "/api/v1/analysis": {"requests": 30, "window": 60},  # 30 req/min
            "default": {"requests": 60, "window": 60}            # 60 req/min default
        }

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with rate limiting"""

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        # Get client identifier (IP address or user ID)
        client_id = self._get_client_id(request)

        # Get rate limit config for this path
        rate_limit = self._get_rate_limit(request.url.path)

        try:
            # Check rate limit
            allowed = await self._check_rate_limit(
                client_id,
                request.url.path,
                rate_limit["requests"],
                rate_limit["window"]
            )

            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded. Please try again later.",
                        "retry_after": rate_limit["window"]
                    },
                    headers={
                        "Retry-After": str(rate_limit["window"]),
                        "X-RateLimit-Limit": str(rate_limit["requests"]),
                        "X-RateLimit-Window": str(rate_limit["window"])
                    }
                )

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            remaining = await self._get_remaining_requests(
                client_id,
                request.url.path,
                rate_limit["requests"],
                rate_limit["window"]
            )

            response.headers["X-RateLimit-Limit"] = str(rate_limit["requests"])
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Window"] = str(rate_limit["window"])

            return response

        except Exception as e:
            logger.error(f"Rate limit middleware error: {e}")
            # On error, allow request (fail open)
            return await call_next(request)

    def _get_client_id(self, request: Request) -> str:
        """
        Get unique client identifier

        In production, you might want to use authenticated user ID
        For now, using IP address
        """
        # Check for forwarded IP (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Use direct client IP
        return request.client.host

    def _get_rate_limit(self, path: str) -> dict:
        """Get rate limit configuration for path"""
        for pattern, config in self.rate_limits.items():
            if pattern == "default":
                continue
            if path.startswith(pattern):
                return config

        return self.rate_limits["default"]

    async def _check_rate_limit(
        self,
        client_id: str,
        path: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Check if request is within rate limit

        Uses sliding window algorithm with Redis
        """
        if not self.redis_client:
            return True  # No Redis, allow all requests

        try:
            key = f"ratelimit:{client_id}:{path}"
            now = time.time()
            window_start = now - window_seconds

            # Remove old entries
            await self.redis_client.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            request_count = await self.redis_client.zcard(key)

            if request_count >= max_requests:
                return False

            # Add current request
            await self.redis_client.zadd(key, {str(now): now})

            # Set expiration
            await self.redis_client.expire(key, window_seconds)

            return True

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Fail open on error

    async def _get_remaining_requests(
        self,
        client_id: str,
        path: str,
        max_requests: int,
        window_seconds: int
    ) -> int:
        """Get number of remaining requests in current window"""
        if not self.redis_client:
            return max_requests

        try:
            key = f"ratelimit:{client_id}:{path}"
            request_count = await self.redis_client.zcard(key)
            return max(0, max_requests - request_count)

        except Exception as e:
            logger.error(f"Get remaining requests error: {e}")
            return max_requests


async def create_rate_limit_middleware():
    """Create rate limit middleware with Redis client"""
    settings = get_settings()

    try:
        redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5
        )
        await redis_client.ping()
        logger.info("Rate limiting middleware initialized with Redis")
        return redis_client

    except Exception as e:
        logger.warning(f"Rate limiting Redis connection failed: {e}")
        logger.warning("Rate limiting will be disabled")
        return None
