from typing import Optional, Any, Dict, Callable
import aio_pika
from infra.rabbitmq.connection import RabbitMQConnection
from infra.config import app_logger


class RabbitMQRepository:
    """Репозиторий для работы с RabbitMQ.

    Предоставляет высокоуровневые методы для работы с очередями, exchange
    и сообщениями RabbitMQ. Все методы являются статическими и используют
    общее соединение через RabbitMQConnection.

    Example:
        >>> # Объявление exchange и очереди
        >>> exchange = await RabbitMQRepository.declare_exchange("events", aio_pika.ExchangeType.DIRECT)
        >>> queue = await RabbitMQRepository.declare_queue("user_events")
        >>> await RabbitMQRepository.bind_queue(queue, "events", "user.*")
        >>>
        >>> # Публикация сообщения
        >>> success = await RabbitMQRepository.publish(
        ...     exchange="events",
        ...     routing_key="user.created",
        ...     message={"user_id": 123, "action": "created"}
        ... )
    """

    @staticmethod
    async def declare_exchange(
        exchange_name: str,
        exchange_type: aio_pika.ExchangeType = aio_pika.ExchangeType.DIRECT,
        durable: bool = True,
    ) -> aio_pika.Exchange:
        """Объявляет exchange с указанными параметрами.

        Если exchange уже существует, возвращает ссылку на существующий exchange.
        Параметры должны совпадать с уже объявленным exchange.

        Args:
            exchange_name: Название exchange. Не может быть пустой строкой.
            exchange_type: Тип exchange. Доступные варианты:
                - DIRECT: Сообщения доставляются в очереди с точным совпадением routing key
                - FANOUT: Сообщения доставляются во все привязанные очереди (broadcast)
                - TOPIC: Сообщения доставляются по pattern matching routing key
                - HEADERS: Сообщения доставляются по совпадению headers
            durable: Если True, exchange сохраняется при перезагрузке RabbitMQ.

        Returns:
            aio_pika.Exchange: Созданный или существующий exchange.

        Raises:
            ValueError: Если exchange_name является пустой строкой.

        Example:
            >>> # Создание direct exchange для точечных сообщений
            >>> exchange = await RabbitMQRepository.declare_exchange(
            ...     "orders",
            ...     aio_pika.ExchangeType.DIRECT,
            ...     durable=True
            ... )
            >>>
            >>> # Создание fanout exchange для уведомлений
            >>> exchange = await RabbitMQRepository.declare_exchange(
            ...     "notifications",
            ...     aio_pika.ExchangeType.FANOUT
            ... )
            >>>
            >>> # Создание topic exchange для гибкой маршрутизации
            >>> exchange = await RabbitMQRepository.declare_exchange(
            ...     "logs",
            ...     aio_pika.ExchangeType.TOPIC
            ... )
        """
        if not exchange_name:
            raise ValueError("Exchange name cannot be empty")

        channel = await RabbitMQConnection.get_channel()
        exchange = await channel.declare_exchange(
            exchange_name, exchange_type, durable=durable
        )
        app_logger.info(
            f"Exchange '{exchange_name}' declared (type: {exchange_type}, durable: {durable})"
        )
        return exchange

    @staticmethod
    async def publish(
        exchange: str,
        routing_key: str,
        message: Any,
        persistent: bool = True,
        exchange_type: aio_pika.ExchangeType = aio_pika.ExchangeType.DIRECT,
    ) -> bool:
        """Публикует сообщение в указанный exchange.

        Args:
            exchange: Название exchange. Если пустая строка, используется default exchange.
            routing_key: Ключ маршрутизации для определения целевой очереди.
            message: Сообщение для отправки. Автоматически преобразуется в строку и кодируется.
            persistent: Если True, сообщение сохраняется на диск и переживает перезагрузку RabbitMQ.
            exchange_type: Тип exchange для создания (если exchange не существует).

        Returns:
            bool: True если сообщение отправлено успешно.

        Raises:
            Exception: Если произошла ошибка при публикации.

        Example:
            >>> # Отправка в default exchange (напрямую в очередь)
            >>> await RabbitMQRepository.publish("", "my_queue", "Hello World")
            >>>
            >>> # Отправка в существующий direct exchange
            >>> await RabbitMQRepository.publish("events", "user.created", "User created")
            >>>
            >>> # Отправка JSON сообщения с сохранением в topic exchange
            >>> import json
            >>> message = json.dumps({"event": "user_created", "id": 123})
            >>> await RabbitMQRepository.publish(
            ...     exchange="logs",
            ...     routing_key="app.user.created",
            ...     message=message,
            ...     persistent=True,
            ...     exchange_type=aio_pika.ExchangeType.TOPIC
            ... )
            >>>
            >>> # Broadcast сообщение через fanout exchange
            >>> await RabbitMQRepository.publish(
            ...     exchange="notifications",
            ...     routing_key="",  # Для fanout routing_key игнорируется
            ...     message="System maintenance",
            ...     exchange_type=aio_pika.ExchangeType.FANOUT
            ... )
        """
        channel = await RabbitMQConnection.get_channel()

        message_body = str(message).encode()
        rabbit_message = aio_pika.Message(
            body=message_body,
            delivery_mode=(
                aio_pika.DeliveryMode.PERSISTENT
                if persistent
                else aio_pika.DeliveryMode.NOT_PERSISTENT
            ),
        )

        if exchange:
            # Объявляем exchange (если не существует) и публикуем
            exchange_obj = await channel.declare_exchange(
                exchange, exchange_type, durable=True
            )
            await exchange_obj.publish(rabbit_message, routing_key=routing_key)
        else:
            # Используем default exchange
            await channel.default_exchange.publish(
                rabbit_message, routing_key=routing_key
            )

        app_logger.info(
            f"Message published to exchange '{exchange if exchange else 'default'}' with routing key '{routing_key}'"
        )
        return True

    @staticmethod
    async def declare_queue(
        queue_name: str,
        durable: bool = True,
        exclusive: bool = False,
        auto_delete: bool = False,
    ) -> aio_pika.RobustQueue:
        """Объявляет очередь с указанными параметрами.

        Если очередь уже существует, возвращает ссылку на существующую очередь.
        Параметры должны совпадать с уже объявленной очередью.

        Args:
            queue_name: Название очереди. Если пустая строка, RabbitMQ создаст уникальное имя.
            durable: Если True, очередь сохраняется при перезагрузке RabbitMQ.
            exclusive: Если True, очередь доступна только текущему соединению и удаляется при его закрытии.
            auto_delete: Если True, очередь удаляется когда все потребители отключаются.

        Returns:
            aio_pika.RobustQueue: Созданная или существующая очередь.

        Example:
            >>> # Создание устойчивой очереди для важных сообщений
            >>> queue = await RabbitMQRepository.declare_queue("important_tasks", durable=True)
            >>>
            >>> # Создание временной очереди для одного потребителя
            >>> temp_queue = await RabbitMQRepository.declare_queue(
            ...     "", exclusive=True, auto_delete=True
            ... )
            >>> print(f"Auto-generated queue name: {temp_queue.name}")
            >>>
            >>> # Очередь с автоматическим удалением при отсутствии потребителей
            >>> queue = await RabbitMQRepository.declare_queue(
            ...     "temp_messages",
            ...     durable=False,
            ...     auto_delete=True
            ... )
        """
        channel = await RabbitMQConnection.get_channel()
        queue = await channel.declare_queue(
            queue_name, durable=durable, exclusive=exclusive, auto_delete=auto_delete
        )
        app_logger.info(
            f"Queue '{queue_name if queue_name else queue.name}' declared (durable: {durable}, exclusive: {exclusive}, auto_delete: {auto_delete})"
        )
        return queue

    @staticmethod
    async def bind_queue(
        queue: aio_pika.RobustQueue,
        exchange: str,
        routing_key: str,
        exchange_type: aio_pika.ExchangeType = aio_pika.ExchangeType.DIRECT,
    ) -> None:
        """Привязывает очередь к exchange с указанным routing key.

        Args:
            queue: Очередь для привязки.
            exchange: Exchange к которому привязывается очередь.
            routing_key: Ключ маршрутизации для фильтрации сообщений.
            exchange_type: Тип exchange для создания (если не существует).

        Example:
            >>> # Привязка очереди к direct exchange
            >>> queue = await RabbitMQRepository.declare_queue("email_notifications")
            >>> await RabbitMQRepository.bind_queue(queue, "notifications", "email")
            >>>
            >>> # Привязка с wildcard routing key для topic exchange
            >>> await RabbitMQRepository.bind_queue(
            ...     queue,
            ...     "logs",
            ...     "*.error",
            ...     exchange_type=aio_pika.ExchangeType.TOPIC
            ... )
            >>>
            >>> # Привязка к fanout exchange (routing_key игнорируется)
            >>> await RabbitMQRepository.bind_queue(
            ...     queue,
            ...     "broadcast",
            ...     "",
            ...     exchange_type=aio_pika.ExchangeType.FANOUT
            ... )
        """
        channel = await RabbitMQConnection.get_channel()
        exchange_obj = await channel.declare_exchange(
            exchange, exchange_type, durable=True
        )
        await queue.bind(exchange_obj, routing_key)
        app_logger.info(
            f"Queue '{queue.name}' bound to exchange '{exchange}' with routing key '{routing_key}'"
        )

    @staticmethod
    async def consume(
        queue_name: str,
        callback: Callable[[aio_pika.IncomingMessage], Any],
        auto_ack: bool = False,
    ) -> None:
        """Начинает потребление сообщений из очереди.

        Args:
            queue_name: Название очереди для потребления.
            callback: Асинхронная функция для обработки сообщений.
                Должна принимать один параметр - aio_pika.IncomingMessage.
            auto_ack: Если True, сообщения автоматически подтверждаются при получении.
                Если False, требуется ручное подтверждение через message.ack().

        Example:
            >>> # Обработчик сообщений с ручным подтверждением
            >>> async def message_handler(message: aio_pika.IncomingMessage):
            ...     try:
            ...         data = message.body.decode()
            ...         print(f"Received: {data}")
            ...         # Обработка сообщения...
            ...         await message.ack()
            ...     except Exception as e:
            ...         print(f"Error processing message: {e}")
            ...         await message.nack(requeue=False)  # Не возвращать в очередь
            ...
            >>> # Запуск потребителя
            >>> await RabbitMQRepository.consume("my_queue", message_handler, auto_ack=False)
            >>>
            >>> # Простой потребитель с автоматическим подтверждением
            >>> async def simple_handler(message: aio_pika.IncomingMessage):
            ...     print(f"Auto-acked message: {message.body.decode()}")
            >>> await RabbitMQRepository.consume("logs", simple_handler, auto_ack=True)
            >>>
            >>> # Обработчик для JSON сообщений
            >>> async def json_handler(message: aio_pika.IncomingMessage):
            ...     import json
            ...     data = json.loads(message.body.decode())
            ...     print(f"JSON received: {data}")
            ...     await message.ack()
            >>> await RabbitMQRepository.consume("json_messages", json_handler)
        """
        channel = await RabbitMQConnection.get_channel()
        queue = await channel.declare_queue(queue_name, durable=True)

        app_logger.info(
            f"Starting consumer for queue '{queue_name}' (auto_ack: {auto_ack})"
        )

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    await callback(message)
                    if not auto_ack:
                        await message.ack()
                    app_logger.debug(f"Message processed from queue '{queue_name}'")
                except Exception as e:
                    app_logger.error(
                        f"Error processing message from queue '{queue_name}': {e}"
                    )
                    if not auto_ack:
                        await message.nack()

    @staticmethod
    async def get_message_count(queue_name: str) -> int:
        """Возвращает количество сообщений в очереди.

        Args:
            queue_name: Название очереди.

        Returns:
            int: Количество сообщений в очереди.

        Example:
            >>> count = await RabbitMQRepository.get_message_count("my_queue")
            >>> print(f"Messages in queue: {count}")
        """
        channel = await RabbitMQConnection.get_channel()
        queue = await channel.declare_queue(queue_name, passive=True)
        return queue.declaration_result.message_count

    @staticmethod
    async def purge_queue(queue_name: str) -> None:
        """Очищает все сообщения из очереди.

        Args:
            queue_name: Название очереди для очистки.

        Example:
            >>> await RabbitMQRepository.purge_queue("old_messages")
            >>> print("Queue purged")
        """
        channel = await RabbitMQConnection.get_channel()
        queue = await channel.declare_queue(queue_name)
        await queue.purge()
        app_logger.info(f"Queue '{queue_name}' purged")
