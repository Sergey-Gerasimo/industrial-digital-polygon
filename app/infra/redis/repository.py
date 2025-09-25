from typing import Optional, Any, Dict
import redis.asyncio as redis
from infra.redis.redis import RedisConnectionPool


class RedisRepository:
    """Репозиторий для асинхронной работы с Redis используя пул соединений.

    Класс предоставляет статические методы для основных операций с Redis.
    Все методы автоматически управляют соединениями через пул.

    Примеры использования:

        >>> # Установка и получение значения
        >>> await RedisRepository.set("user:1", "John", expire=3600)
        >>> name = await RedisRepository.get("user:1")

        >>> # Работа с хэшами
        >>> await RedisRepository.hset("profile:1", {"name": "Alice", "age": "25"})
        >>> profile = await RedisRepository.hgetall("profile:1")

        >>> # Работа со списками
        >>> await RedisRepository.lpush("queue:emails", "test@example.com")
        >>> email = await RedisRepository.rpop("queue:emails")

    Attributes:
        Не содержит атрибутов, так как все методы статические.
    """

    @staticmethod
    def _get_client() -> redis.Redis:
        """Получает клиент Redis из пула соединений.

        Returns:
            redis.Redis: Клиент Redis для выполнения операций.

        Note:
            Этот метод используется внутренне другими методами класса.
            Не требуется вызывать напрямую в бизнес-логике.
        """
        pool = RedisConnectionPool.get_pool()
        return redis.Redis(connection_pool=pool)

    @staticmethod
    async def ping() -> bool:
        """Проверяет соединение с Redis сервером.

        Returns:
            bool: True если соединение активно, False в противном случае.

        Example:
            >>> is_connected = await RedisRepository.ping()
            >>> if not is_connected:
            ...     print("Redis недоступен")
        """
        client = RedisRepository._get_client()
        try:
            return await client.ping()
        finally:
            await client.close()

    @staticmethod
    async def set(key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Устанавливает значение для ключа.

        Args:
            key: Ключ для установки значения.
            value: Значение для сохранения.
            expire: Время жизни ключа в секундах (опционально).

        Returns:
            bool: True если операция успешна, False в противном случае.

        Example:
            >>> # Сохранение на 1 час
            >>> await RedisRepository.set("session:123", "user_data", expire=3600)
            >>> # Сохранение навсегда
            >>> await RedisRepository.set("config:version", "1.0.0")
        """
        client = RedisRepository._get_client()
        try:
            result = await client.set(key, value, ex=expire)
            return bool(result)
        finally:
            await client.close()

    @staticmethod
    async def setex(key: str, time: int, value: Any) -> bool:
        """Устанавливает значение с временем жизни (TTL).

        Аналог команды SETEX в Redis. Устанавливает значение и TTL атомарно.

        Args:
            key: Ключ для установки значения.
            time: Время жизни ключа в секундах.
            value: Значение для сохранения.

        Returns:
            bool: True если операция успешна, False в противном случае.

        Example:
            >>> # Временный токен на 5 минут
            >>> await RedisRepository.setex("auth:token", 300, "secret_token")
            >>> # Кэш на 1 час
            >>> await RedisRepository.setex("page:cache", 3600, "<html>...</html>")
        """
        client = RedisRepository._get_client()
        try:
            result = await client.setex(key, time, value)
            return bool(result)
        finally:
            await client.close()

    @staticmethod
    async def get(key: str) -> Optional[str]:
        """Получает значение по ключу.

        Args:
            key: Ключ для получения значения.

        Returns:
            Optional[str]: Значение ключа или None если ключ не существует.

        Example:
            >>> value = await RedisRepository.get("user:profile")
            >>> if value:
            ...     print(f"Найдено: {value}")
            ... else:
            ...     print("Ключ не найден")
        """
        client = RedisRepository._get_client()
        try:
            return await client.get(key)
        finally:
            await client.close()

    @staticmethod
    async def delete(*keys: str) -> int:
        """Удаляет один или несколько ключей.

        Args:
            *keys: Произвольное количество ключей для удаления.

        Returns:
            int: Количество удаленных ключей.

        Example:
            >>> # Удаление одного ключа
            >>> count = await RedisRepository.delete("temp:data")
            >>> # Удаление нескольких ключей
            >>> count = await RedisRepository.delete("key1", "key2", "key3")
        """
        client = RedisRepository._get_client()
        try:
            return await client.delete(*keys)
        finally:
            await client.close()

    @staticmethod
    async def exists(key: str) -> bool:
        """Проверяет существование ключа.

        Args:
            key: Ключ для проверки.

        Returns:
            bool: True если ключ существует, False в противном случае.

        Example:
            >>> if await RedisRepository.exists("user:session"):
            ...     print("Сессия активна")
            ... else:
            ...     print("Сессия истекла")
        """
        client = RedisRepository._get_client()
        try:
            return await client.exists(key) > 0
        finally:
            await client.close()

    @staticmethod
    async def hset(key: str, mapping: Dict[str, Any]) -> int:
        """Устанавливает поля хэша.

        Args:
            key: Ключ хэша.
            mapping: Словарь с полями и значениями для установки.

        Returns:
            int: Количество установленных полей.

        Example:
            >>> user_data = {"name": "John", "email": "john@example.com", "age": "30"}
            >>> await RedisRepository.hset("user:1", user_data)
        """
        client = RedisRepository._get_client()
        try:
            return await client.hset(key, mapping=mapping)
        finally:
            await client.close()

    @staticmethod
    async def hgetall(key: str) -> Dict[str, Any]:
        """Получает все поля и значения хэша.

        Args:
            key: Ключ хэша.

        Returns:
            Dict[str, Any]: Словарь со всеми полями хэша.

        Example:
            >>> profile = await RedisRepository.hgetall("user:1")
            >>> print(f"Имя: {profile['name']}, Email: {profile['email']}")
        """
        client = RedisRepository._get_client()
        try:
            return await client.hgetall(key)
        finally:
            await client.close()

    @staticmethod
    async def expire(key: str, seconds: int) -> bool:
        """Устанавливает время жизни ключа.

        Args:
            key: Ключ для установки TTL.
            seconds: Время жизни в секундах.

        Returns:
            bool: True если TTL установлен, False если ключ не существует.

        Example:
            >>> # Продлить сессию на 30 минут
            >>> await RedisRepository.expire("user:session", 1800)
        """
        client = RedisRepository._get_client()
        try:
            return await client.expire(key, seconds)
        finally:
            await client.close()

    @staticmethod
    async def incr(key: str) -> int:
        """Увеличивает числовое значение ключа на 1.

        Args:
            key: Ключ с числовым значением.

        Returns:
            int: Новое значение после увеличения.

        Example:
            >>> # Счетчик просмотров
            >>> views = await RedisRepository.incr("page:views:1")
            >>> print(f"Просмотров: {views}")
        """
        client = RedisRepository._get_client()
        try:
            return await client.incr(key)
        finally:
            await client.close()

    @staticmethod
    async def lpush(key: str, *values: Any) -> int:
        """Добавляет значения в начало списка.

        Args:
            key: Ключ списка.
            *values: Значения для добавления.

        Returns:
            int: Длина списка после добавления.

        Example:
            >>> # Добавление в очередь задач
            >>> length = await RedisRepository.lpush("queue:tasks", "task1", "task2")
        """
        client = RedisRepository._get_client()
        try:
            return await client.lpush(key, *values)
        finally:
            await client.close()

    @staticmethod
    async def rpop(key: str) -> Optional[str]:
        """Извлекает значение из конца списка.

        Args:
            key: Ключ списка.

        Returns:
            Optional[str]: Значение из конца списка или None если список пуст.

        Example:
            >>> # Обработка очереди (FIFO)
            >>> task = await RedisRepository.rpop("queue:tasks")
            >>> if task:
            ...     process_task(task)
        """
        client = RedisRepository._get_client()
        try:
            return await client.rpop(key)
        finally:
            await client.close()

    @staticmethod
    async def sadd(key: str, *members: Any) -> int:
        """Добавляет элементы в множество.

        Args:
            key: Ключ множества.
            *members: Элементы для добавления.

        Returns:
            int: Количество добавленных элементов (исключая дубликаты).

        Example:
            >>> # Уникальные теги
            >>> await RedisRepository.sadd("post:1:tags", "python", "redis", "async")
        """
        client = RedisRepository._get_client()
        try:
            return await client.sadd(key, *members)
        finally:
            await client.close()

    @staticmethod
    async def smembers(key: str) -> set:
        """Получает все элементы множества.

        Args:
            key: Ключ множества.

        Returns:
            set: Множество всех элементов.

        Example:
            >>> tags = await RedisRepository.smembers("post:1:tags")
            >>> print(f"Теги: {', '.join(tags)}")
        """
        client = RedisRepository._get_client()
        try:
            return await client.smembers(key)
        finally:
            await client.close()
