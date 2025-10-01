import asyncio
from infra.rabbitmq.connection import RabbitMQConnection


async def safe_rabbitmq_close():
    """Безопасное закрытие соединения RabbitMQ"""
    try:
        await RabbitMQConnection.close()
        # Даем время на завершение фоновых задач
        await asyncio.sleep(0.2)
    except Exception as e:
        print(f"Safe close warning: {e}")


async def ensure_clean_connection():
    """Обеспечивает чистое состояние соединения"""
    await safe_rabbitmq_close()
    # Сбрасываем синглтон
    RabbitMQConnection._connection = None
    RabbitMQConnection._channel = None


async def cleanup_test_queues(queue_names):
    try:
        for queue_name in queue_names:
            try:
                channel = await RabbitMQConnection.get_channel()
                queue = await channel.get_queue(queue_name, ensure=False)
                if queue:
                    await queue.delete()
            except Exception as e:
                print(f"Warning: Could not delete queue {queue_name}: {e}")
    except Exception as e:
        print(f"Warning: Cleanup error: {e}")


async def cleanup_test_exchanges(exchange_names):
    """Вспомогательный метод для очистки тестовых exchange."""
    try:
        for exchange_name in exchange_names:
            try:
                channel = await RabbitMQConnection.get_channel()
                exchange = await channel.get_exchange(exchange_name, ensure=False)
                if exchange:
                    await exchange.delete()
            except Exception as e:
                print(f"Warning: Could not delete exchange {exchange_name}: {e}")
    except Exception as e:
        print(f"Warning: Cleanup error: {e}")
