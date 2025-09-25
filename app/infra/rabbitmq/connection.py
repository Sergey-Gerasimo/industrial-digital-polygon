import aio_pika
from typing import AsyncGenerator, Optional
from infra.config.settings import settings
from infra.config import app_logger


class RabbitMQConnection:
    """Класс для управления подключением к RabbitMQ.

    Реализует singleton паттерн для соединения и канала RabbitMQ.
    Обеспечивает повторное использование соединений и автоматическое
    восстановление при обрывах связи.

    Attributes:
        _connection: Статическая переменная для хранения соединения с RabbitMQ.
        _channel: Статическая переменная для хранения канала RabbitMQ.

    Example:
        >>> # Получение канала для работы
        >>> channel = await RabbitMQConnection.get_channel()
        >>> await channel.default_exchange.publish(message, routing_key="test")
    """

    _connection: Optional[aio_pika.RobustConnection] = None
    _channel: Optional[aio_pika.RobustChannel] = None

    @classmethod
    async def get_connection(cls) -> aio_pika.RobustConnection:
        """Возвращает активное подключение к RabbitMQ.

        Создает новое соединение если оно не существует или закрыто.
        Использует настройки из конфигурации приложения.

        Returns:
            aio_pika.RobustConnection: Активное соединение с RabbitMQ.

        Raises:
            ConnectionError: Если не удалось установить соединение.

        Example:
            >>> connection = await RabbitMQConnection.get_connection()
            >>> print(f"Connected to RabbitMQ: {not connection.is_closed}")
        """

        if cls._connection is None or cls._connection.is_closed:
            cls._connection = await aio_pika.connect_robust(
                settings.rabbitmq.url, timeout=settings.rabbitmq.timeout
            )
            app_logger.info("RabbitMQ connection established")
        return cls._connection

    @classmethod
    async def get_channel(cls) -> aio_pika.RobustChannel:
        """Возвращает канал для работы с RabbitMQ.

        Создает новый канал если он не существует или закрыт.
        Канал используется для выполнения операций с очередями и exchange.

        Returns:
            aio_pika.RobustChannel: Канал для работы с RabbitMQ.

        Example:
            >>> channel = await RabbitMQConnection.get_channel()
            >>> queue = await channel.declare_queue("my_queue")
            >>> await queue.purge()
        """

        if cls._channel is None or cls._channel.is_closed:
            connection = await cls.get_connection()
            cls._channel = await connection.channel()
            app_logger.info("RabbitMQ channel created")
        return cls._channel

    @classmethod
    async def close(cls):
        """Закрывает подключение к RabbitMQ и освобождает ресурсы.

        Рекомендуется вызывать при завершении работы приложения
        для корректного закрытия соединений.

        Example:
            >>> await RabbitMQConnection.close()
            >>> print("RabbitMQ connections closed")
        """
        if cls._channel:
            await cls._channel.close()
        if cls._connection:
            await cls._connection.close()
        app_logger.info("RabbitMQ connection closed")


async def get_rabbitmq_channel() -> AsyncGenerator[aio_pika.RobustChannel, None]:
    """Dependency для FastAPI - получаем канал из пула.

    Используется для внедрения зависимости RabbitMQ канала в эндпоинты FastAPI.
    Автоматически управляет жизненным циклом канала в рамках запроса.

    Yields:
        aio_pika.RobustChannel: Канал RabbitMQ для использования в эндпоинте.

    Raises:
        Exception: Если произошла ошибка при получении канала.

    Example:
        >>> from fastapi import Depends
        >>>
        >>> @app.post("/publish/{message}")
        >>> async def publish_message(
        ...     message: str,
        ...     channel: aio_pika.RobustChannel = Depends(get_rabbitmq_channel)
        ... ):
        ...     rabbit_message = aio_pika.Message(body=message.encode())
        ...     await channel.default_exchange.publish(rabbit_message, routing_key="queue")
        ...     return {"status": "message sent"}
    """

    channel = await RabbitMQConnection.get_channel()
    try:
        yield channel
    except Exception as e:
        app_logger.error(f"RabbitMQ channel error: {e}")
        raise
