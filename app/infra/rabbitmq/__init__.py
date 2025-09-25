"""Пакет для асинхронной работы с RabbitMQ через единое управляемое соединение.

Пакет предоставляет высокоуровневый интерфейс для работы с RabbitMQ
с singleton подключением, автоматическим реконнектом и поддержкой всех типов exchange.

Основные компоненты:
    - RabbitMQConnection: Менеджер singleton соединения и канала
    - RabbitMQRepository: Репозиторий с высокоуровневыми методами для работы с очередями
    - get_rabbitmq_channel: Dependency для FastAPI

Примеры использования:

    Быстрая работа через репозиторий:
        >>> from infra.rabbitmq import RabbitMQRepository
        >>>
        >>> # Публикация сообщений
        >>> await RabbitMQRepository.publish("events", "user.created", {"id": 123})
        >>> await RabbitMQRepository.publish("logs", "app.error", "Error message")
        >>>
        >>> # Работа с очередями
        >>> queue = await RabbitMQRepository.declare_queue("user_events")
        >>> await RabbitMQRepository.bind_queue(queue, "events", "user.*")

    Использование в FastAPI endpoint:
        >>> from fastapi import Depends
        >>> from infra.rabbitmq import get_rabbitmq_channel
        >>>
        >>> @app.post("/publish/{message}")
        >>> async def publish_message(
        ...     message: str,
        ...     channel = Depends(get_rabbitmq_channel)
        ... ):
        ...     rabbit_message = aio_pika.Message(body=message.encode())
        ...     await channel.default_exchange.publish(rabbit_message, routing_key="queue")
        ...     return {"status": "message sent"}

    Потребление сообщений:
        >>> async def message_handler(message):
        ...     data = message.body.decode()
        ...     print(f"Received: {data}")
        ...     await message.ack()
        >>>
        >>> await RabbitMQRepository.consume("user_events", message_handler)

    Управление соединением:
        >>> from infra.rabbitmq import RabbitMQConnection
        >>>
        >>> # Получение канала вручную
        >>> channel = await RabbitMQConnection.get_channel()
        >>>
        >>> # Закрытие соединения при завершении приложения
        >>> await RabbitMQConnection.close()

Особенности:
    - Singleton подключение для всего приложения
    - Автоматическое восстановление соединения
    - Поддержка всех типов RabbitMQ exchange
    - Durable сообщения и очереди
    - Интеграция с FastAPI через dependencies

Перед использованием убедитесь, что настройки RabbitMQ указаны в config.settings.

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
