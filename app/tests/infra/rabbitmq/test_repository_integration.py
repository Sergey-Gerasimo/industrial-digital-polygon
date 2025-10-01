import pytest
import asyncio
import aio_pika
import json
from typing import List, Any
from infra.rabbitmq.connection import RabbitMQConnection
from infra.rabbitmq import RabbitMQRepository
from infra.config import app_logger
from tests.infra.rabbitmq.async_utils import (
    safe_rabbitmq_close,
    ensure_clean_connection,
    cleanup_test_queues,
    cleanup_test_exchanges,
)


@pytest.mark.integration
@pytest.mark.rabbitmq
@pytest.mark.asyncio
class TestRabbitMQRepositoryIntegration:
    """Интеграционные тесты для RabbitMQRepository с использованием существующей инфраструктуры."""

    async def test_declare_exchange_success(self):
        """Тест успешного создания exchange."""
        # Arrange
        await ensure_clean_connection()
        test_exchange_name = f"test_exchange_{id(self)}"

        try:
            # Act
            exchange = await RabbitMQRepository.declare_exchange(
                test_exchange_name,
                aio_pika.ExchangeType.DIRECT,
                durable=False,  # Для тестов используем недолговечный exchange
            )

            # Assert
            assert exchange is not None
            assert exchange.name == test_exchange_name
            assert isinstance(exchange, aio_pika.Exchange)

        finally:
            # Cleanup
            await cleanup_test_exchanges([test_exchange_name])
            await safe_rabbitmq_close()

    async def test_declare_exchange_invalid_name(self):
        """Тест создания exchange с пустым именем."""
        # Arrange
        await ensure_clean_connection()

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="Exchange name cannot be empty"):
                await RabbitMQRepository.declare_exchange("")

        finally:
            await safe_rabbitmq_close()

    async def test_declare_exchange_invalid_name(self):
        """Тест создания exchange с пустым именем."""
        # Arrange
        await ensure_clean_connection()

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="Exchange name cannot be empty"):
                await RabbitMQRepository.declare_exchange("")

        finally:
            await safe_rabbitmq_close()

    async def test_declare_queue_success(self):
        """Тест успешного создания очереди."""
        # Arrange
        await ensure_clean_connection()
        test_queue_name = f"test_queue_{id(self)}"

        try:
            # Act
            queue = await RabbitMQRepository.declare_queue(
                test_queue_name,
                durable=False,  # Для тестов используем недолговечную очередь
                exclusive=False,
                auto_delete=True,  # Автоматически удаляем после тестов
            )

            # Assert
            assert queue is not None
            assert queue.name == test_queue_name
            assert isinstance(queue, aio_pika.RobustQueue)

        finally:
            await cleanup_test_queues([test_queue_name])
            await safe_rabbitmq_close()

    async def test_declare_queue_auto_generated_name(self):
        """Тест создания очереди с автоматически сгенерированным именем."""
        # Arrange
        await ensure_clean_connection()

        try:
            # Act
            queue = await RabbitMQRepository.declare_queue(
                "", exclusive=True, auto_delete=True
            )

            # Assert
            assert queue is not None
            assert queue.name != ""
            assert isinstance(queue, aio_pika.RobustQueue)

            # Очищаем автоматически созданную очередь
            await cleanup_test_queues([queue.name])

        finally:
            await safe_rabbitmq_close()

    async def test_publish_and_consume_message_default_exchange(self):
        """Тест публикации и потребления сообщения через default exchange."""
        # Arrange
        await ensure_clean_connection()
        test_queue_name = f"test_queue_{id(self)}"
        test_message = "Test message content"
        received_messages: List[str] = []
        consume_task = None

        async def message_handler(message):
            nonlocal received_messages
            app_logger.debug(f"Received message: {message.body.decode()}")
            received_messages.append(message.body.decode())
            await message.ack()

        try:
            # Act - объявляем очередь с явными параметрами

            # Act - потребляем сообщение
            consume_task = asyncio.create_task(
                RabbitMQRepository.consume(
                    test_queue_name, message_handler, auto_ack=False
                )
            )

            await asyncio.sleep(1)

            # Act - публикуем сообщение
            publish_result = await RabbitMQRepository.publish(
                exchange="",
                routing_key=test_queue_name,
                message=test_message,
                persistent=False,  # Для тестов не используем сохранение
            )

            # Ждем обработки сообщения с таймаутом
            for _ in range(10):  # 10 попыток по 0.5 секунды
                if received_messages:
                    break
                await asyncio.sleep(0.5)

            # Assert
            assert publish_result is True
            assert len(received_messages) == 1
            assert received_messages[0] == test_message

        finally:
            # Аккуратно останавливаем потребителя
            if consume_task and not consume_task.done():
                consume_task.cancel()
                try:
                    await consume_task
                except (asyncio.CancelledError, Exception):
                    pass

            await cleanup_test_queues([test_queue_name])
            await safe_rabbitmq_close()

    async def test_consume_from_custom_exchange_direct(self):
        """Тест потребления сообщений из custom direct exchange."""
        await ensure_clean_connection()
        test_exchange_name = f"test_exchange_{id(self)}"
        test_queue_name = f"test_queue_{id(self)}"
        test_routing_key = "user.created"
        test_message = "User created message"
        received_messages: List[str] = []
        message_received = asyncio.Event()

        async def message_handler(message):
            received_messages.append(message.body.decode())
            await message.ack()
            message_received.set()

        try:
            # Создаем custom direct exchange
            exchange = await RabbitMQRepository.declare_exchange(
                test_exchange_name, aio_pika.ExchangeType.DIRECT, durable=False
            )

            # Создаем и привязываем очередь к exchange с конкретным routing key
            queue = await RabbitMQRepository.declare_queue(
                test_queue_name, auto_delete=True
            )

            await RabbitMQRepository.bind_queue(
                queue,
                test_exchange_name,
                test_routing_key,
                aio_pika.ExchangeType.DIRECT,
            )

            publish_result = await RabbitMQRepository.publish(
                exchange=test_exchange_name,
                routing_key=test_routing_key,
                message=test_message,
                persistent=False,
                exchange_type=aio_pika.ExchangeType.DIRECT,
            )

            # Запускаем потребителя
            consume_task = asyncio.create_task(
                RabbitMQRepository.consume(
                    test_queue_name, message_handler, auto_ack=False
                )
            )

            # Ждем получения сообщения
            try:
                await asyncio.wait_for(message_received.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                pass

            # Останавливаем потребитель
            consume_task.cancel()
            try:
                await consume_task
            except (asyncio.CancelledError, Exception):
                pass

            # Assert
            assert publish_result is True
            assert (
                len(received_messages) == 1
            ), f"Expected 1 message, but got {len(received_messages)}"
            assert received_messages[0] == test_message

        finally:
            await cleanup_test_queues([test_queue_name])
            await cleanup_test_exchanges([test_exchange_name])
            await safe_rabbitmq_close()

    async def test_fanout_exchange_broadcast(self):
        """Тест broadcast сообщений через FANOUT exchange."""
        await ensure_clean_connection()
        test_exchange_name = f"test_fanout_{id(self)}"
        test_queues = [f"test_queue_{i}_{id(self)}" for i in range(3)]
        received_messages = {queue: [] for queue in test_queues}
        events = {queue: asyncio.Event() for queue in test_queues}
        consume_tasks = []

        async def create_handler(queue_name):
            async def handler(message):
                received_messages[queue_name].append(message.body.decode())
                await message.ack()
                events[queue_name].set()

            return handler

        try:
            # Создаем FANOUT exchange
            exchange = await RabbitMQRepository.declare_exchange(
                test_exchange_name, aio_pika.ExchangeType.FANOUT, durable=False
            )

            # Создаем и привязываем несколько очередей
            for queue_name in test_queues:
                queue = await RabbitMQRepository.declare_queue(
                    queue_name, auto_delete=True
                )
                await RabbitMQRepository.bind_queue(
                    queue, test_exchange_name, "", aio_pika.ExchangeType.FANOUT
                )

                # Запускаем потребителей
                handler = await create_handler(queue_name)
                task = asyncio.create_task(
                    RabbitMQRepository.consume(queue_name, handler, auto_ack=False)
                )
                consume_tasks.append(task)

            await asyncio.sleep(2)  # Даем время потребителям запуститься

            # Публикуем broadcast сообщение
            broadcast_message = "Broadcast message to all queues"
            publish_result = await RabbitMQRepository.publish(
                exchange=test_exchange_name,
                routing_key="",  # Для FANOUT не важно
                message=broadcast_message,
                persistent=False,
                exchange_type=aio_pika.ExchangeType.FANOUT,
            )

            # Ждем получения сообщения всеми очередями
            for queue_name in test_queues:
                try:
                    await asyncio.wait_for(events[queue_name].wait(), timeout=10.0)
                except asyncio.TimeoutError:
                    app_logger.warning(f"Timeout for queue {queue_name}")

            # Assert
            assert publish_result is True
            for queue_name in test_queues:
                assert len(received_messages[queue_name]) == 1
                assert received_messages[queue_name][0] == broadcast_message

        finally:
            # Останавливаем потребителей
            for task in consume_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except (asyncio.CancelledError, Exception):
                        pass

            await cleanup_test_queues(test_queues)
            await cleanup_test_exchanges([test_exchange_name])
            await safe_rabbitmq_close()

    async def test_json_message_processing(self):
        """Тест обработки JSON сообщений."""
        await ensure_clean_connection()
        test_queue = f"test_json_{id(self)}"
        test_data = {"event": "user_created", "user_id": 123, "timestamp": "2023-01-01"}
        received_data = None
        message_received = asyncio.Event()

        async def json_handler(message):
            nonlocal received_data
            received_data = json.loads(message.body.decode())
            await message.ack()
            message_received.set()

        try:
            # Запускаем потребитель для JSON сообщений
            consume_task = asyncio.create_task(
                RabbitMQRepository.consume(test_queue, json_handler, auto_ack=False)
            )

            await asyncio.sleep(1)

            # Публикуем JSON сообщение
            await RabbitMQRepository.publish(
                "", test_queue, json.dumps(test_data), persistent=False
            )

            # Ждем получения
            try:
                await asyncio.wait_for(message_received.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                pass

            # Assert
            assert received_data is not None
            assert received_data["event"] == test_data["event"]
            assert received_data["user_id"] == test_data["user_id"]

        finally:
            if "consume_task" in locals() and not consume_task.done():
                consume_task.cancel()
                try:
                    await consume_task
                except (asyncio.CancelledError, Exception):
                    pass

            await cleanup_test_queues([test_queue])
            await safe_rabbitmq_close()

    async def test_large_message_handling(self):
        """Тест обработки больших сообщений."""
        await ensure_clean_connection()
        test_queue = f"test_large_{id(self)}"
        large_message = "X" * 1024 * 1024  # 1MB сообщение
        received_message = None
        message_received = asyncio.Event()

        async def large_message_handler(message):
            nonlocal received_message
            received_message = message.body.decode()
            await message.ack()
            message_received.set()

        try:
            consume_task = asyncio.create_task(
                RabbitMQRepository.consume(
                    test_queue, large_message_handler, auto_ack=False
                )
            )

            await asyncio.sleep(1)

            # Публикуем большое сообщение
            await RabbitMQRepository.publish(
                "", test_queue, large_message, persistent=False
            )

            # Ждем получения
            try:
                await asyncio.wait_for(message_received.wait(), timeout=15.0)
            except asyncio.TimeoutError:
                pass

            # Assert
            assert received_message is not None
            assert len(received_message) == len(large_message)
            assert received_message == large_message

        finally:
            if "consume_task" in locals() and not consume_task.done():
                consume_task.cancel()
                try:
                    await consume_task
                except (asyncio.CancelledError, Exception):
                    pass

            await cleanup_test_queues([test_queue])
            await safe_rabbitmq_close()
