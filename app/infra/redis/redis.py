from typing import AsyncGenerator, Optional
import redis.asyncio as redis

from infra.config.settings import settings
from infra.config import app_logger


class RedisConnectionPool:
    """Класс для управления пулом соединений Redis.

    Реализует singleton паттерн для пула соединений. Обеспечивает
    эффективное переиспользование соединений с Redis.

    Attributes:
        _pool: Статическая переменная для хранения пула соединений.
    """

    _pool: Optional[redis.ConnectionPool] = None

    @classmethod
    def get_pool(cls) -> redis.ConnectionPool:
        """Возвращает пул соединений, создавая его при первом вызове.

        Returns:
            redis.ConnectionPool: Пул соединений с настройками из конфигурации.

        Example:
            >>> pool = RedisConnectionPool.get_pool()
        """
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
        """Закрывает пул соединений и освобождает ресурсы.

        Example:
            >>> await RedisConnectionPool.close_pool()
        """
        if cls._pool is not None:
            await cls._pool.disconnect()
            cls._pool = None


class RedisClient:
    """Контекстный менеджер для работы с Redis клиентом.

    Обеспечивает автоматическое управление жизненным циклом клиента
    при использовании в конструкции with.

    Attributes:
        _client: Экземпляр Redis клиента.
    """

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    async def __aenter__(self) -> redis.Redis:
        """Вход в контекстный менеджер.

        Returns:
            redis.Redis: Клиент Redis из пула соединений.

        Example:
            >>> async with RedisClient() as client:
            ...     await client.set("key", "value")
        """
        pool = RedisConnectionPool.get_pool()
        self._client = redis.Redis(connection_pool=pool)
        return self._client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера.

        Args:
            exc_type: Тип исключения (если было).
            exc_val: Значение исключения.
            exc_tb: Traceback исключения.
        """
        if self._client:
            await self._client.close()


async def get_redis_client() -> AsyncGenerator[redis.Redis, None]:
    """Dependency для FastAPI для внедрения Redis клиента.

    Yields:
        redis.Redis: Клиент Redis для использования в endpoint.

    Raises:
        Exception: Если не удалось установить соединение с Redis.

    Example:
        >>> @router.get("/items/{item_id}")
        >>> async def read_item(
        ...     item_id: int,
        ...     redis: redis.Redis = Depends(get_redis_client)
        ... ):
        ...     value = await redis.get(f"item:{item_id}")
        ...     return {"value": value}
    """
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
