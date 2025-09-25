from typing import Optional, Any, Dict
import redis.asyncio as redis
from infra.redis.redis import RedisConnectionPool


class RedisRepository:
    """Репозиторий для работы с Redis используя пул соединений"""

    @staticmethod
    def _get_client() -> redis.Redis:
        """Получаем клиент из пула соединений"""
        pool = RedisConnectionPool.get_pool()
        return redis.Redis(connection_pool=pool)

    @staticmethod
    async def ping() -> bool:
        """Проверка соединения с Redis"""
        client = RedisRepository._get_client()
        try:
            return await client.ping()
        finally:
            await client.close()

    @staticmethod
    async def set(key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Установка значения"""
        client = RedisRepository._get_client()
        try:
            result = await client.set(key, value, ex=expire)
            return bool(result)
        finally:
            await client.close()

    @staticmethod
    async def setex(key: str, time: int, value: Any) -> bool:
        """Установка значения с TTL"""
        client = RedisRepository._get_client()
        try:
            result = await client.setex(key, time, value)
            return bool(result)
        finally:
            await client.close()

    @staticmethod
    async def get(key: str) -> Optional[str]:
        """Получение значения"""
        client = RedisRepository._get_client()
        try:
            return await client.get(key)
        finally:
            await client.close()

    @staticmethod
    async def delete(*keys: str) -> int:
        """Удаление ключей"""
        client = RedisRepository._get_client()
        try:
            return await client.delete(*keys)
        finally:
            await client.close()

    @staticmethod
    async def exists(key: str) -> bool:
        """Проверка существования ключа"""
        client = RedisRepository._get_client()
        try:
            return await client.exists(key) > 0
        finally:
            await client.close()

    @staticmethod
    async def hset(key: str, mapping: Dict[str, Any]) -> int:
        """Установка хэша"""
        client = RedisRepository._get_client()
        try:
            return await client.hset(key, mapping=mapping)
        finally:
            await client.close()

    @staticmethod
    async def hgetall(key: str) -> Dict[str, Any]:
        """Получение всего хэша"""
        client = RedisRepository._get_client()
        try:
            return await client.hgetall(key)
        finally:
            await client.close()

    @staticmethod
    async def expire(key: str, seconds: int) -> bool:
        """Установка TTL"""
        client = RedisRepository._get_client()
        try:
            return await client.expire(key, seconds)
        finally:
            await client.close()

    @staticmethod
    async def incr(key: str) -> int:
        """Инкремент значения"""
        client = RedisRepository._get_client()
        try:
            return await client.incr(key)
        finally:
            await client.close()

    @staticmethod
    async def lpush(key: str, *values: Any) -> int:
        """Добавление в список слева"""
        client = RedisRepository._get_client()
        try:
            return await client.lpush(key, *values)
        finally:
            await client.close()

    @staticmethod
    async def rpop(key: str) -> Optional[str]:
        """Извлечение из списка справа"""
        client = RedisRepository._get_client()
        try:
            return await client.rpop(key)
        finally:
            await client.close()

    @staticmethod
    async def sadd(key: str, *members: Any) -> int:
        """Добавление в множество"""
        client = RedisRepository._get_client()
        try:
            return await client.sadd(key, *members)
        finally:
            await client.close()

    @staticmethod
    async def smembers(key: str) -> set:
        """Получение множества"""
        client = RedisRepository._get_client()
        try:
            return await client.smembers(key)
        finally:
            await client.close()
