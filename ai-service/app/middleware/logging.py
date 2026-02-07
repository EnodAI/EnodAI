"""
Logging middleware with request tracing and correlation IDs
"""
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive logging middleware
    Logs all requests with timing, correlation IDs, and user context
    """

    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id

        # Start timer
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"→ {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"← {request.method} {request.url.path} {response.status_code} ({duration:.3f}s)",
                extra={
                    "correlation_id": correlation_id,
                    "status_code": response.status_code,
                    "duration": duration,
                }
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Process-Time"] = f"{duration:.3f}"

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Log error
            logger.error(
                f"✗ {request.method} {request.url.path} ERROR ({duration:.3f}s): {str(e)}",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "duration": duration,
                },
                exc_info=True
            )

            raise
