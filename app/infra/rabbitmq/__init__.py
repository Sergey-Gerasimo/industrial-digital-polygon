"""Пакет для асинхронной работы с RabbitMQ через единое управляемое соединение.

Пакет предоставляет высокоуровневый интерфейс для работы с RabbitMQ
с singleton подключением, автоматическим реконнектом и поддержкой всех типов exchange.

Основные компоненты:
    - RabbitMQConnection: Менеджер singleton соединения и канала
    - RabbitMQRepository: Репозиторий с высокоуровневыми методами для работы с очередями
    - get_rabbitmq_channel: Dependency для FastAPI

Особенности:
    - Автоматическое восстановление соединений (RobustConnection)
    - Пул соединений для эффективного использования ресурсов
    - Поддержка всех типов exchange (DIRECT, FANOUT, TOPIC, HEADERS)
    - Интеграция с системой логирования приложения
    - Dependency Injection для FastAPI

Примеры использования:

    Быстрая отправка сообщений:
        >>> from infra.rabbitmq import RabbitMQRepository
        >>>
        >>> # Отправка в default exchange
        >>> await RabbitMQRepository.publish("", "my_queue", "Hello World")
        >>>
        >>> # Отправка в конкретный exchange
        >>> await RabbitMQRepository.publish("events", "user.created", {"id": 123})

    Работа с очередями и exchange:
        >>> from infra.rabbitmq import RabbitMQRepository
        >>> import aio_pika
        >>>
        >>> # Создание exchange и очереди
        >>> exchange = await RabbitMQRepository.declare_exchange(
        ...     "notifications",
        ...     aio_pika.ExchangeType.FANOUT
        ... )
        >>> queue = await RabbitMQRepository.declare_queue("email_notifications")
        >>> await RabbitMQRepository.bind_queue(queue, "notifications", "")

    Использование в FastAPI:
        >>> from fastapi import Depends
        >>> from infra.rabbitmq import get_rabbitmq_channel
        >>> import aio_pika
        >>>
        >>> @app.post("/publish/{message}")
        >>> async def publish_message(
        ...     message: str,
        ...     channel: aio_pika.RobustChannel = Depends(get_rabbitmq_channel)
        ... ):
        ...     await channel.default_exchange.publish(
        ...         aio_pika.Message(body=message.encode()),
        ...         routing_key="test_queue"
        ...     )
        ...     return {"status": "sent"}

    Запуск потребителя сообщений:
        >>> from infra.rabbitmq import RabbitMQRepository
        >>>
        >>> async def message_handler(message):
        ...     print(f"Received: {message.body.decode()}")
        ...     await message.ack()
        >>>
        >>> # Запуск потребителя в фоновой задаче
        >>> await RabbitMQRepository.consume("my_queue", message_handler)

Настройки подключения берутся из config.settings.rabbitmq.

Version: 1.0.0
"""

from .connection import RabbitMQConnection, get_rabbitmq_channel
from .repository import RabbitMQRepository

__version__ = "1.0.0"

__all__ = [
    "RabbitMQConnection",
    "RabbitMQRepository",
    "get_rabbitmq_channel",
]
