import pytest
import aio_pika
from unittest.mock import AsyncMock, patch


@pytest.mark.infra
@pytest.mark.rabbitmq
@pytest.mark.asyncio
class TestRabbitMQConnectionUnit:

    async def test_get_connection_first_time(
        self, mock_settings, mock_aio_pika, mock_logger, rabbitmq_connection
    ):
        """Тест получения соединения при первом вызове"""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika

        # Act
        connection = await rabbitmq_connection.get_connection()

        # Assert
        mock_pika.connect_robust.assert_called_once_with(
            "amqp://test:test@localhost:5672/", timeout=30
        )
        assert connection == mock_connection
        mock_logger.info.assert_called_with("RabbitMQ connection established")

    async def test_get_connection_reuses_existing(
        self, mock_settings, mock_aio_pika, rabbitmq_connection
    ):
        """Тест повторного использования существующего соединения"""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika

        # Act - первый вызов
        connection1 = await rabbitmq_connection.get_connection()
        # Act - второй вызов
        connection2 = await rabbitmq_connection.get_connection()

        # Assert
        mock_pika.connect_robust.assert_called_once()
        assert connection1 == connection2 == mock_connection

    async def test_get_channel_first_time(
        self, mock_settings, mock_aio_pika, mock_logger, rabbitmq_connection
    ):
        """Тест получения канала при первом вызове"""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika

        # Act
        channel = await rabbitmq_connection.get_channel()

        # Assert
        mock_connection.channel.assert_called_once()
        assert channel == mock_channel
        mock_logger.info.assert_any_call("RabbitMQ channel created")

    async def test_get_channel_reuses_existing(
        self, mock_settings, mock_aio_pika, rabbitmq_connection
    ):
        """Тест повторного использования существующего канала"""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika

        # Act - первый вызов
        channel1 = await rabbitmq_connection.get_channel()
        # Act - второй вызов
        channel2 = await rabbitmq_connection.get_channel()

        # Assert
        mock_connection.channel.assert_called_once()
        assert channel1 == channel2 == mock_channel

    async def test_close_connection_and_channel(
        self, mock_settings, mock_aio_pika, mock_logger, rabbitmq_connection
    ):
        """Тест закрытия соединения и канала"""
        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika

        # Act - получить соединение и канал
        await rabbitmq_connection.get_connection()
        await rabbitmq_connection.get_channel()

        # Act - закрыть соединение и канал
        await rabbitmq_connection.close()

        # Assert
        mock_channel.close.assert_awaited_once()
        mock_connection.close.assert_awaited_once()
        mock_logger.info.assert_any_call("RabbitMQ channel closed")
        mock_logger.info.assert_any_call("RabbitMQ connection closed")

    async def test_get_rabbitmq_channel_dependency(
        self, mock_settings, mock_aio_pika, rabbitmq_connection
    ):
        """Тест зависимости get_rabbitmq_channel"""
        from infra.rabbitmq.connection import get_rabbitmq_channel

        # Arrange
        mock_pika, mock_connection, mock_channel = mock_aio_pika

        # Act
        async for channel in get_rabbitmq_channel():
            # Assert внутри генератора
            assert channel == mock_channel

        mock_connection.channel.assert_called_once()
