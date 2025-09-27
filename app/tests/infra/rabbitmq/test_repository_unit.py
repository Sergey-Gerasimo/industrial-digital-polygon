import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import aio_pika
from infra.rabbitmq.repository import RabbitMQRepository
from infra.rabbitmq.connection import RabbitMQConnection
from infra.config import app_logger


@pytest.mark.infra
@pytest.mark.rabbitmq
@pytest.mark.asyncio
class TestRabbitMQRepositoryUnit:

    @pytest.fixture
    def mock_queue(self):
        """Правильный мок очереди с queue.iterator()."""
        mock_queue = AsyncMock(spec=aio_pika.RobustQueue)
        mock_queue.name = "test_queue"

        # Мок для асинхронного контекстного менеджера iterator()
        mock_queue_iter = AsyncMock()

        # Создаем mock сообщение
        mock_message = AsyncMock(spec=aio_pika.IncomingMessage)
        mock_message.body = b"test message"
        mock_message.ack = AsyncMock()
        mock_message.nack = AsyncMock()

        # Создаем асинхронный итератор для сообщений
        async def message_generator():
            yield mock_message

        # Настраиваем асинхронный контекстный менеджер
        mock_queue_iter.__aenter__ = AsyncMock(return_value=message_generator())
        mock_queue_iter.__aexit__ = AsyncMock(return_value=None)

        # Мок для queue.iterator() возвращает контекстный менеджер
        mock_queue.iterator.return_value = mock_queue_iter

        return mock_queue

    @pytest.fixture
    def mock_queue_multiple_messages(self):
        """Мок очереди с несколькими сообщениями."""
        mock_queue = AsyncMock(spec=aio_pika.RobustQueue)
        mock_queue.name = "test_queue"

        # Создаем несколько сообщений
        messages = [
            AsyncMock(
                spec=aio_pika.IncomingMessage,
                body=b"message 1",
                ack=AsyncMock(),
                nack=AsyncMock(),
            ),
            AsyncMock(
                spec=aio_pika.IncomingMessage,
                body=b"message 2",
                ack=AsyncMock(),
                nack=AsyncMock(),
            ),
        ]

        async def message_generator():
            for msg in messages:
                yield msg

        mock_queue_iter = AsyncMock()
        mock_queue_iter.__aenter__ = AsyncMock(return_value=message_generator())
        mock_queue_iter.__aexit__ = AsyncMock(return_value=None)
        mock_queue.iterator.return_value = mock_queue_iter

        return mock_queue

    @pytest.fixture
    def mock_message(self):
        """Мок входящего сообщения."""
        mock_message = AsyncMock(spec=aio_pika.IncomingMessage)
        mock_message.body = b"test message"
        mock_message.ack = AsyncMock()
        mock_message.nack = AsyncMock()
        return mock_message

    async def test_declare_exchange_success(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
    ):
        """Тест успешного объявления exchange."""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_exchange = AsyncMock()
        mock_channel.declare_exchange.return_value = mock_exchange

        # Act
        result = await RabbitMQRepository.declare_exchange(
            "test_exchange", aio_pika.ExchangeType.DIRECT
        )

        # Assert
        mock_channel.declare_exchange.assert_called_once_with(
            "test_exchange", aio_pika.ExchangeType.DIRECT, durable=True
        )
        assert result == mock_exchange

    async def test_declare_exchange_empty_name(self):
        """Тест объявления exchange с пустым именем."""
        # Act & Assert
        with pytest.raises(ValueError, match="Exchange name cannot be empty"):
            await RabbitMQRepository.declare_exchange("")

    async def test_declare_exchange_with_parameters(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
    ):
        """Тест объявления exchange с различными параметрами."""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_exchange = AsyncMock()
        mock_channel.declare_exchange.return_value = mock_exchange

        # Act
        result = await RabbitMQRepository.declare_exchange(
            "test_exchange", aio_pika.ExchangeType.TOPIC, durable=False
        )

        # Assert
        mock_channel.declare_exchange.assert_called_once_with(
            "test_exchange", aio_pika.ExchangeType.TOPIC, durable=False
        )

    async def test_publish_to_exchange_existing(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
    ):
        """Тест публикации сообщения в существующий exchange."""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_exchange = AsyncMock()
        mock_channel.get_exchange.return_value = mock_exchange

        test_message = "test message content"

        # Act
        result = await RabbitMQRepository.publish(
            exchange="test_exchange", routing_key="test.key", message=test_message
        )

        # Assert
        mock_channel.get_exchange.assert_called_once_with(
            name="test_exchange", ensure=False
        )
        mock_exchange.publish.assert_called_once()
        assert result is True

    async def test_publish_to_exchange_not_existing(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
    ):
        """Тест публикации сообщения в несуществующий exchange (должен создать)."""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_exchange = AsyncMock()

        # Симулируем, что exchange не существует
        mock_channel.get_exchange.side_effect = (
            aio_pika.exceptions.ChannelNotFoundEntity()
        )
        mock_channel.declare_exchange.return_value = mock_exchange

        test_message = "test message content"

        # Act
        result = await RabbitMQRepository.publish(
            exchange="test_exchange", routing_key="test.key", message=test_message
        )

        # Assert
        mock_channel.get_exchange.assert_called_once_with(
            name="test_exchange", ensure=False
        )
        mock_channel.declare_exchange.assert_called_once_with(
            "test_exchange", aio_pika.ExchangeType.DIRECT, durable=True
        )
        mock_exchange.publish.assert_called_once()
        assert result is True

    async def test_publish_to_default_exchange(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
    ):
        """Тест публикации в default exchange."""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        test_message = "test message"

        # Act
        result = await RabbitMQRepository.publish(
            exchange="", routing_key="test_queue", message=test_message
        )

        # Assert
        mock_channel.default_exchange.publish.assert_called_once()
        assert result is True

    async def test_publish_persistent_message(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
    ):
        """Тест публикации persistent сообщения."""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_exchange = AsyncMock()
        mock_channel.get_exchange.return_value = mock_exchange

        # Act
        await RabbitMQRepository.publish(
            exchange="test", routing_key="test.key", message="test", persistent=True
        )

        # Assert - проверяем что сообщение создано с PERSISTENT delivery_mode
        call_args = mock_exchange.publish.call_args
        published_message = call_args[0][0]  # Первый аргумент вызова
        assert published_message.delivery_mode == aio_pika.DeliveryMode.PERSISTENT

    async def test_publish_non_persistent_message(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
    ):
        """Тест публикации non-persistent сообщения."""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_exchange = AsyncMock()
        mock_channel.get_exchange.return_value = mock_exchange

        # Act
        await RabbitMQRepository.publish(
            exchange="test", routing_key="test.key", message="test", persistent=False
        )

        # Assert
        call_args = mock_exchange.publish.call_args
        published_message = call_args[0][0]
        assert published_message.delivery_mode == aio_pika.DeliveryMode.NOT_PERSISTENT

    async def test_declare_queue(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
    ):
        """Тест объявления очереди."""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_queue = AsyncMock()
        mock_channel.declare_queue.return_value = mock_queue

        # Act
        result = await RabbitMQRepository.declare_queue("test_queue")

        # Assert
        mock_channel.declare_queue.assert_called_once_with(
            "test_queue", durable=True, exclusive=False, auto_delete=False
        )
        assert result == mock_queue

    async def test_declare_queue_with_parameters(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
    ):
        """Тест объявления очереди с различными параметрами."""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_queue = AsyncMock()
        mock_channel.declare_queue.return_value = mock_queue

        # Act
        result = await RabbitMQRepository.declare_queue(
            "temp_queue", durable=False, exclusive=True, auto_delete=True
        )

        # Assert
        mock_channel.declare_queue.assert_called_once_with(
            "temp_queue", durable=False, exclusive=True, auto_delete=True
        )

    async def test_declare_anonymous_queue(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
    ):
        """Тест объявления анонимной очереди."""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_queue = AsyncMock()
        mock_queue.name = "amq.gen-12345"
        mock_channel.declare_queue.return_value = mock_queue

        # Act
        result = await RabbitMQRepository.declare_queue("")

        # Assert
        mock_channel.declare_queue.assert_called_once_with(
            "", durable=True, exclusive=False, auto_delete=False
        )

    async def test_bind_queue_existing_exchange(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
        mock_queue: AsyncMock,
    ):
        """Тест привязки очереди к существующему exchange."""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_exchange = AsyncMock()
        mock_channel.get_exchange.return_value = mock_exchange

        # Act
        await RabbitMQRepository.bind_queue(
            queue=mock_queue, exchange="test_exchange", routing_key="test.key"
        )

        # Assert
        mock_channel.get_exchange.assert_called_once_with(
            name="test_exchange", ensure=True
        )
        mock_queue.bind.assert_called_once_with(mock_exchange, "test.key")

    async def test_bind_queue_new_exchange(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
        mock_queue: AsyncMock,
    ):
        """Тест привязки очереди к новому exchange (должен создать)."""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_exchange = AsyncMock()

        # Симулируем, что exchange не существует
        mock_channel.get_exchange.side_effect = (
            aio_pika.exceptions.ChannelNotFoundEntity()
        )
        mock_channel.declare_exchange.return_value = mock_exchange

        # Act
        await RabbitMQRepository.bind_queue(
            queue=mock_queue, exchange="test_exchange", routing_key="test.key"
        )

        # Assert
        mock_channel.get_exchange.assert_called_once_with(
            name="test_exchange", ensure=True
        )
        mock_channel.declare_exchange.assert_called_once_with(
            "test_exchange", aio_pika.ExchangeType.DIRECT, durable=True
        )
        mock_queue.bind.assert_called_once_with(mock_exchange, "test.key")

    async def test_consume_existing_queue(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
        mock_queue: AsyncMock,
    ):
        """Тест потребления сообщений из существующей очереди."""
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_channel.declare_queue.return_value = mock_queue

        callback_called = False
        received_message = None

        async def test_callback(message):
            nonlocal callback_called, received_message
            callback_called = True
            received_message = message

        # Act
        # Используем таймаут, чтобы тест не зависал
        try:
            await asyncio.wait_for(
                RabbitMQRepository.consume("test_queue", test_callback, auto_ack=False),
                timeout=0.5,
            )
        except asyncio.TimeoutError:
            pass

        # Assert
        mock_channel.declare_queue.assert_called_once_with("test_queue", passive=True)
        assert callback_called is True
        assert received_message is not None
        assert received_message.body == b"test message"
        received_message.ack.assert_called_once()

    async def test_consume_new_queue(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
        mock_queue: AsyncMock,
    ):
        """Тест потребления сообщений из несуществующей очереди (должен создать)."""
        mock_pika, mock_connection, mock_channel = mock_aio_pika

        # Симулируем, что очередь не существует
        mock_channel.declare_queue.side_effect = [
            aio_pika.exceptions.ChannelNotFoundEntity(),  # Первый вызов (passive=True)
            mock_queue,  # Второй вызов (создание очереди)
        ]

        callback_called = asyncio.Event()

        async def test_callback(message):
            callback_called.set()

        # Act
        # Запускаем consume в отдельной задаче
        consume_task = asyncio.create_task(
            RabbitMQRepository.consume("test_queue", test_callback, auto_ack=False)
        )

        # Ждем немного и отменяем задачу
        await asyncio.sleep(0.1)
        consume_task.cancel()

        try:
            await consume_task
        except asyncio.CancelledError:
            pass

        # Assert
        assert mock_channel.declare_queue.call_count == 2
        mock_channel.declare_queue.assert_any_call("test_queue", passive=True)
        mock_channel.declare_queue.assert_any_call(
            "test_queue", durable=True, auto_delete=False
        )

    async def test_get_message_count(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
    ):
        """Тест получения количества сообщений в очереди."""
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_queue = AsyncMock()
        mock_declaration = MagicMock()
        mock_declaration.message_count = 5
        mock_queue.declaration_result = mock_declaration
        mock_channel.declare_queue.return_value = mock_queue

        # Act
        result = await RabbitMQRepository.get_message_count("test_queue")

        # Assert
        mock_channel.declare_queue.assert_called_once_with("test_queue", passive=True)
        assert result == 5

    async def test_purge_queue(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
    ):
        """Тест очистки очереди."""
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_queue = AsyncMock()
        mock_channel.declare_queue.return_value = mock_queue

        # Act
        await RabbitMQRepository.purge_queue("test_queue")

        # Assert
        mock_channel.declare_queue.assert_called_once_with("test_queue")
        mock_queue.purge.assert_called_once()

    async def test_consume_with_exception_in_callback(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
        mock_queue: AsyncMock,
    ):
        """Тест consume с исключением в callback функции."""
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_channel.declare_queue.return_value = mock_queue

        async def faulty_callback(message):
            raise Exception("Callback error")

        with patch("infra.rabbitmq.repository.app_logger") as mock_logger:
            # Act
            try:
                await asyncio.wait_for(
                    RabbitMQRepository.consume(
                        "test_queue", faulty_callback, auto_ack=False
                    ),
                    timeout=0.5,
                )
            except asyncio.TimeoutError:
                pass

            # Assert
            mock_logger.error.assert_called()

    async def test_consume_auto_ack(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
        mock_queue: AsyncMock,
    ):
        """Тест consume с auto_ack=True."""
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_channel.declare_queue.return_value = mock_queue

        callback_called = False

        async def test_callback(message):
            nonlocal callback_called
            callback_called = True

        # Act
        try:
            await asyncio.wait_for(
                RabbitMQRepository.consume("test_queue", test_callback, auto_ack=True),
                timeout=0.5,
            )
        except asyncio.TimeoutError:
            pass

        # Assert
        assert callback_called is True
        # При auto_ack=True ack не должен вызываться вручную
        # (проверяется через то, что нет вызова message.ack())

    async def test_publish_with_different_exchange_type(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
    ):
        """Тест публикации с указанием типа exchange."""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_exchange = AsyncMock()
        mock_channel.get_exchange.side_effect = (
            aio_pika.exceptions.ChannelNotFoundEntity()
        )
        mock_channel.declare_exchange.return_value = mock_exchange

        # Act
        result = await RabbitMQRepository.publish(
            exchange="test_topic",
            routing_key="test.key",
            message="test",
            exchange_type=aio_pika.ExchangeType.TOPIC,
        )

        # Assert
        mock_channel.declare_exchange.assert_called_once_with(
            "test_topic", aio_pika.ExchangeType.TOPIC, durable=True
        )
        assert result is True

    async def test_bind_queue_with_different_exchange_type(
        self,
        mock_aio_pika: tuple[MagicMock | AsyncMock, AsyncMock, AsyncMock],
        mock_settings: MagicMock | AsyncMock,
        mock_queue: AsyncMock,
    ):
        """Тест привязки с указанием типа exchange."""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika
        mock_exchange = AsyncMock()
        mock_channel.get_exchange.side_effect = (
            aio_pika.exceptions.ChannelNotFoundEntity()
        )
        mock_channel.declare_exchange.return_value = mock_exchange

        # Act
        await RabbitMQRepository.bind_queue(
            queue=mock_queue,
            exchange="test_topic",
            routing_key="test.*",
            exchange_type=aio_pika.ExchangeType.TOPIC,
        )

        # Assert
        mock_channel.declare_exchange.assert_called_once_with(
            "test_topic", aio_pika.ExchangeType.TOPIC, durable=True
        )
