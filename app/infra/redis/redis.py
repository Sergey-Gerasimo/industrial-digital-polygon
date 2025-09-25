from typing import AsyncGenerator, Optional
import redis.asyncio as redis

from infra.config.settings import settings
from infra.config import app_logger


class RedisConnectionPool:
    _pool: Optional[redis.ConnectionPool] = None

    @classmethod
    def get_pool(cls) -> redis.ConnectionPool:
        if cls._pool is None:
            cls._pool = redis.ConnectionPool.from_url(
                settings.redis.url,
                max_connections=settings.redis.max_connections,
                decode_responses=settings.redis.decode_responses,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30,
            )
        return cls._pool

    @classmethod
    async def close_pool(cls):
        if cls._pool is not None:
            await cls._pool.disconnect()
            cls._pool = None


class RedisClient:
    def __init__(self):
        self._client: Optional[redis.Redis] = None

    async def __aenter__(self) -> redis.Redis:
        pool = RedisConnectionPool.get_pool()
        self._client = redis.Redis(connection_pool=pool)
        return self._client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.close()


async def get_redis_client() -> AsyncGenerator[redis.Redis, None]:
    """Dependency for FastAPI - получаем клиент из пула"""
    pool = RedisConnectionPool.get_pool()
    client = redis.Redis(connection_pool=pool)
    try:
        await client.ping()
        yield client
    except redis.RedisError as e:
        app_logger.error(f"Redis connection error: {e}")
        raise Exception(f"Redis connection error: {e}")
    finally:
        await client.close()
