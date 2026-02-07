from fastapi import FastAPI
from app.routers import analysis, health, auth
from app.database import Database
from app.redis_client import RedisConsumer
from app.scheduler import scheduler
from app.middleware.rate_limit import RateLimitMiddleware, create_rate_limit_middleware
from app.middleware.logging import LoggingMiddleware
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EnodAI AI Service",
    description="AI-powered anomaly detection and alert analysis service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "EnodAI Team",
        "email": "support@enodai.dev",
    },
    license_info={
        "name": "MIT",
    },
)

# Add middlewares
app.add_middleware(LoggingMiddleware)

# Add rate limiting middleware
rate_limit_redis = None

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(health.router, tags=["health"])

consumer = RedisConsumer()

@app.on_event("startup")
async def startup_event():
    global rate_limit_redis

    logger.info("Starting up AI Service...")
    await Database.connect()

    # Initialize rate limiting
    # Note: Rate limit middleware is disabled for now as it requires dynamic initialization
    # rate_limit_redis = await create_rate_limit_middleware()
    # if rate_limit_redis:
    #     app.add_middleware(RateLimitMiddleware, redis_client=rate_limit_redis)

    # Start Redis consumer in background
    asyncio.create_task(consumer.start_consuming())

    # Start scheduler for model retraining
    await scheduler.start()

    logger.info("✅ AI Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    global rate_limit_redis

    logger.info("Shutting down AI Service...")
    await consumer.stop()
    await scheduler.stop()
    await Database.disconnect()

    # Close rate limiting Redis connection
    if rate_limit_redis:
        await rate_limit_redis.close()

    logger.info("✅ AI Service shutdown complete")