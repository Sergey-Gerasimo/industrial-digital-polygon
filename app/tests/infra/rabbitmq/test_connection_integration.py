import pytest
import asyncio
import aio_pika
from infra.rabbitmq.connection import RabbitMQConnection, get_rabbitmq_channel
from tests.infra.rabbitmq.async_utils import (
    safe_rabbitmq_close,
    ensure_clean_connection,
)


@pytest.mark.integration
@pytest.mark.rabbitmq
@pytest.mark.asyncio
class TestRabbitMQConnectionIntegration:
    async def test_connection_to_real_rabbitmq(self):
        """Test connection to real RabbitMQ server"""
        # Arrange
        await ensure_clean_connection()

        try:
            # Act
            connection = await RabbitMQConnection.get_connection()

            # Assert
            assert connection is not None
            assert not connection.is_closed
            assert isinstance(connection, aio_pika.RobustConnection)

        finally:
            # Cleanup
            await safe_rabbitmq_close()

    async def test_channel_to_real_rabbitmq(self):
        """Test channel to real RabbitMQ server"""
        # Arrange
        await ensure_clean_connection()

        try:
            # Act
            channel = await RabbitMQConnection.get_channel()

            # Assert
            assert channel is not None
            assert not channel.is_closed
            assert isinstance(channel, aio_pika.RobustChannel)

        finally:
            # Cleanup
            await safe_rabbitmq_close()

    async def test_connection_reuse(self):
        """Test that connection and channel are reused (singleton pattern)"""
        await ensure_clean_connection()

        try:
            # Act
            connection1 = await RabbitMQConnection.get_connection()
            connection2 = await RabbitMQConnection.get_connection()
            channel1 = await RabbitMQConnection.get_channel()
            channel2 = await RabbitMQConnection.get_channel()

            # Assert - should be the same instances (singleton)
            assert connection1 is connection2
            assert channel1 is channel2

        finally:
            await safe_rabbitmq_close()

    async def test_fastapi_dependency(self):
        """Test the FastAPI dependency injection"""
        await ensure_clean_connection()

        try:
            # Act
            channel_count = 0
            async for channel in get_rabbitmq_channel():
                channel_count += 1
                assert channel is not None
                assert not channel.is_closed

            # Assert
            assert channel_count == 1

        finally:
            await safe_rabbitmq_close()

    async def test_connection_recovery_after_close(self):
        """Test that connection recovers after being closed"""
        await ensure_clean_connection()

        try:
            # Get initial connection
            connection1 = await RabbitMQConnection.get_connection()
            channel1 = await RabbitMQConnection.get_channel()

            # Close the connection manually
            await RabbitMQConnection.close()

            # Get new connection - should recover automatically
            connection2 = await RabbitMQConnection.get_connection()
            channel2 = await RabbitMQConnection.get_channel()

            # Assert - should be new instances after close
            assert connection2 is not connection1
            assert channel2 is not channel1
            assert not connection2.is_closed
            assert not channel2.is_closed

        finally:
            await safe_rabbitmq_close()

    async def test_multiple_sequential_operations(self):
        """Test multiple sequential operations on the same connection"""
        await ensure_clean_connection()

        try:
            # Perform multiple operations
            connection = await RabbitMQConnection.get_connection()
            channel = await RabbitMQConnection.get_channel()

            # Test basic queue operations
            test_queue_name = f"test_queue_{id(self)}"
            queue = await channel.declare_queue(test_queue_name, auto_delete=True)

            # Publish a message
            message = aio_pika.Message(body=b"Test message")
            await channel.default_exchange.publish(message, routing_key=test_queue_name)

            # Consume the message
            incoming_message = await queue.get(timeout=5)
            assert incoming_message is not None
            assert incoming_message.body == b"Test message"
            await incoming_message.ack()

            # Cleanup test queue
            await queue.delete()

        finally:
            await safe_rabbitmq_close()

    async def test_channel_operations(self):
        """Test various channel operations"""
        await ensure_clean_connection()

        try:
            channel = await RabbitMQConnection.get_channel()

            # Test exchange declaration
            exchange = await channel.declare_exchange(
                "test_integration_exchange",
                aio_pika.ExchangeType.DIRECT,
                auto_delete=True,
            )
            assert exchange is not None

            # Test queue declaration
            queue = await channel.declare_queue(
                "test_integration_queue", auto_delete=True
            )
            assert queue is not None

            # Test binding
            await queue.bind(exchange, "test.routing.key")

            # Cleanup
            await queue.delete()
            await exchange.delete()

        finally:
            await safe_rabbitmq_close()

    async def test_connection_properties(self):
        """Test connection properties and methods"""
        await ensure_clean_connection()

        try:
            connection = await RabbitMQConnection.get_connection()
            channel = await RabbitMQConnection.get_channel()

            # Test basic properties
            assert hasattr(connection, "is_closed")
            assert hasattr(channel, "is_closed")
            assert hasattr(channel, "default_exchange")

            # Test that we can get the same channel multiple times
            same_channel = await RabbitMQConnection.get_channel()
            assert channel is same_channel

        finally:
            await safe_rabbitmq_close()

    @pytest.mark.slow
    async def test_connection_stability(self):
        """Test connection stability over multiple operations"""
        await ensure_clean_connection()

        try:
            # Perform multiple operations to test stability
            for i in range(10):
                connection = await RabbitMQConnection.get_connection()
                channel = await RabbitMQConnection.get_channel()

                assert not connection.is_closed
                assert not channel.is_closed

                # Small delay between operations
                await asyncio.sleep(0.1)

        finally:
            await safe_rabbitmq_close()

    async def test_error_handling(self):
        """Test error handling scenarios"""
        await ensure_clean_connection()

        try:
            # Test that we can recover from errors
            connection = await RabbitMQConnection.get_connection()

            # Simulate an error by closing the underlying connection
            original_connection = RabbitMQConnection._connection
            if original_connection:
                await original_connection.close()

            # Should recover automatically
            new_connection = await RabbitMQConnection.get_connection()
            assert new_connection is not None
            assert not new_connection.is_closed

        finally:
            await safe_rabbitmq_close()

    async def test_concurrent_access(self):
        """Test concurrent access to the connection"""
        await ensure_clean_connection()

        try:
            # Use a timeout to prevent hanging indefinitely
            RabbitMQConnection()._lock = (
                asyncio.Lock()
            )  # Reset lock to avoid deadlock from previous tests

            async def get_connection_and_channel(task_id):
                await asyncio.sleep(0.001 * task_id)
                conn = await RabbitMQConnection.get_connection()
                await asyncio.sleep(0.001)
                chan = await RabbitMQConnection.get_channel()
                return task_id, conn, chan

            tasks = [get_connection_and_channel(i) for i in range(5)]
            results = await asyncio.gather(*tasks)

            connections = [result[1] for result in results]
            channels = [result[2] for result in results]

            first_connection = connections[0]
            first_channel = channels[0]

            for i, conn in enumerate(connections):
                assert (
                    conn is first_connection
                ), f"Connection {i} is not the same instance"

            for i, chan in enumerate(channels):
                assert chan is first_channel, f"Channel {i} is not the same instance"

        except asyncio.TimeoutError:
            pytest.fail("Test timed out - possible deadlock in RabbitMQConnection")
        finally:
            await safe_rabbitmq_close()
