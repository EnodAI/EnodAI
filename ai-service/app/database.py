import asyncpg
import asyncio
from loguru import logger
from app.config import get_settings
from typing import List, Any

class DatabasePool:
    _pool = None

    @classmethod
    async def get_pool(cls):
        if cls._pool is None:
            settings = get_settings()
            # FIX: Ensure protocol compatibility for asyncpg (postgres://)
            dsn = settings.database_url.replace("postgresql://", "postgres://")

            # FIX: Add retry logic for database connection
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    cls._pool = await asyncpg.create_pool(
                        dsn=dsn,
                        min_size=5,
                        max_size=20,
                        command_timeout=10
                    )
                    logger.info("Database connection pool created")
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to create database pool after {max_retries} attempts: {e}")
                        raise
                    logger.warning(f"Database connection failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in 5s...")
                    await asyncio.sleep(5)
        return cls._pool

    @classmethod
    async def close_pool(cls):
        if cls._pool:
            try:
                await cls._pool.close()
                logger.info("Database connection pool closed")
            except Exception as e:
                logger.error(f"Error closing database pool: {e}")
            finally:
                cls._pool = None


class Database:
    """
    Database wrapper class for CRUD operations
    Provides high-level interface for database interactions
    """

    @staticmethod
    async def connect():
        """Initialize database connection pool"""
        await DatabasePool.get_pool()
        logger.info("Database connected")

    @staticmethod
    async def disconnect():
        """Close database connection pool"""
        await DatabasePool.close_pool()
        logger.info("Database disconnected")

    @staticmethod
    async def fetch(query: str, *args) -> List[dict]:
        """
        Fetch multiple rows from database

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            List of row dictionaries
        """
        try:
            pool = await DatabasePool.get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Database fetch error: {e}")
            raise

    @staticmethod
    async def fetchrow(query: str, *args) -> dict:
        """
        Fetch single row from database

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            Row dictionary or None
        """
        try:
            pool = await DatabasePool.get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Database fetchrow error: {e}")
            raise

    @staticmethod
    async def fetchval(query: str, *args) -> Any:
        """
        Fetch single value from database

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            Single value
        """
        try:
            pool = await DatabasePool.get_pool()
            async with pool.acquire() as conn:
                return await conn.fetchval(query, *args)
        except Exception as e:
            logger.error(f"Database fetchval error: {e}")
            raise

    @staticmethod
    async def execute(query: str, *args) -> str:
        """
        Execute query (INSERT, UPDATE, DELETE)

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            Query result status
        """
        try:
            pool = await DatabasePool.get_pool()
            async with pool.acquire() as conn:
                return await conn.execute(query, *args)
        except Exception as e:
            logger.error(f"Database execute error: {e}")
            raise

    @staticmethod
    async def executemany(query: str, args_list: List[tuple]) -> None:
        """
        Execute query multiple times with different parameters

        Args:
            query: SQL query string
            args_list: List of parameter tuples
        """
        try:
            pool = await DatabasePool.get_pool()
            async with pool.acquire() as conn:
                await conn.executemany(query, args_list)
        except Exception as e:
            logger.error(f"Database executemany error: {e}")
            raise


async def get_db_pool():
    """Get database connection pool"""
    return await DatabasePool.get_pool()