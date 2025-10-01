"""Пакет для асинхронной работы с Redis через пул соединений.

Пакет предоставляет высокоуровневый интерфейс для работы с Redis
с автоматическим управлением соединениями, health checks и интеграцией с FastAPI.

Основные компоненты:
    - RedisConnectionPool: Управление пулом соединений
    - RedisClient: Контекстный менеджер для работы с клиентом
    - get_redis_client: Dependency для FastAPI
    - RedisRepository: Репозиторий с высокоуровневыми методами

Примеры использования:

    Быстрая работа через репозиторий:
        >>> from infra.redis import RedisRepository
        >>> await RedisRepository.set("ключ", "значение", expire=3600)
        >>> value = await RedisRepository.get("ключ")

    Использование в FastAPI endpoint:
        >>> from fastapi import Depends
        >>> from infra.redis import get_redis_client
        >>>
        >>> @app.get("/cache/{key}")
        >>> async def get_data(key: str, redis = Depends(get_redis_client)):
        ...     value = await redis.get(key)
        ...     return {"value": value}

    Работа через контекстный менеджер:
        >>> from infra.redis import RedisClient
        >>>
        >>> async with RedisClient() as client:
        ...     await client.set("key", "value")
        ...     result = await client.get("key")

Настройки подключения берутся из config.settings.redis.

Version: 1.0.0
"""

from infra.redis.redis import RedisConnectionPool, RedisClient, get_redis_client
from infra.redis.repository import RedisRepository

__version__ = "1.0.0"

__all__ = [
    "RedisConnectionPool",
    "RedisClient",
    "get_redis_client",
    "RedisRepository",
]
