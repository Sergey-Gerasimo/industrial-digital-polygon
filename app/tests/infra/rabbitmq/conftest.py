# tests/infra/rabbitmq/conftest.py
import pytest
import asyncio
import aio_pika
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import os
import sys


@pytest.fixture
def mock_settings():
    """Фикстура для мокирования настроек RabbitMQ"""
    with patch("infra.rabbitmq.connection.settings") as mock_settings:
        mock_settings.rabbitmq.url = "amqp://test:test@localhost:5672/"
        mock_settings.rabbitmq.timeout = 30
        yield mock_settings


@pytest.fixture
def mock_aio_pika():
    """Фикстура для мокирования aio_pika модуля - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    with patch("infra.rabbitmq.connection.aio_pika") as mock_pika:
        # Создаем настоящие AsyncMock объекты, которые можно await
        mock_connection = AsyncMock()
        mock_connection.is_closed = False
        mock_connection.close = AsyncMock()
        mock_connection.channel = AsyncMock()

        mock_channel = AsyncMock()
        mock_channel.is_closed = False
        mock_channel.close = AsyncMock()

        # Настраиваем возвращаемые значения
        mock_connection.channel.return_value = mock_channel

        # Мокируем connect_robust чтобы возвращал Future с нашим mock_connection
        future_conn = asyncio.Future()
        future_conn.set_result(mock_connection)
        mock_pika.connect_robust.return_value = future_conn

        # Мокируем классы для isinstance проверок
        mock_pika.RobustConnection = aio_pika.RobustConnection
        mock_pika.RobustChannel = aio_pika.RobustChannel

        yield mock_pika, mock_connection, mock_channel


@pytest.fixture
def mock_logger():
    """Фикстура для мокирования логгера"""
    with patch("infra.rabbitmq.connection.app_logger") as mock_logger:
        yield mock_logger


@pytest.fixture(autouse=True)
def reset_rabbitmq_singleton():
    """Автоматически сбрасываем синглтон RabbitMQConnection перед каждым тестом"""
    from infra.rabbitmq.connection import RabbitMQConnection

    # Сохраняем оригинальные значения (на случай если они были установлены)
    original_connection = RabbitMQConnection._connection
    original_channel = RabbitMQConnection._channel

    # Сбрасываем синглтон
    RabbitMQConnection._connection = None
    RabbitMQConnection._channel = None

    yield

    # Восстанавливаем оригинальные значения
    RabbitMQConnection._connection = original_connection
    RabbitMQConnection._channel = original_channel


@pytest.fixture
def rabbitmq_connection():
    """Фикстура предоставляет доступ к классу RabbitMQConnection"""
    from infra.rabbitmq.connection import RabbitMQConnection

    return RabbitMQConnection


# Остальные фикстуры остаются без изменений...
@pytest.fixture
async def rabbitmq_test_config():
    """Конфигурация для интеграционных тестов RabbitMQ"""
    return {
        "test_queue_prefix": "test_queue_",
        "test_exchange_prefix": "test_exchange_",
        "test_routing_key": "test.routing.key",
    }


@pytest.fixture
async def rabbitmq_integration_setup():
    """Улучшенная фикстура для настройки интеграционных тестов"""
    from infra.rabbitmq.connection import RabbitMQConnection

    # Убедимся что соединение корректно закрыто перед тестом
    try:
        await RabbitMQConnection.close()
    except Exception:
        pass  # Игнорируем ошибки при закрытии

    yield

    # Корректно закрываем соединение после теста
    try:
        await RabbitMQConnection.close()
    except Exception:
        pass


@pytest.fixture
async def rabbitmq_cleanup():
    """Фикстура для очистки тестовых ресурсов с правильным управлением соединениями"""
    from infra.rabbitmq.connection import RabbitMQConnection

    async def cleaner(queue_names=None, exchange_names=None):
        queue_names = queue_names or []
        exchange_names = exchange_names or []

        try:
            # Получаем канал для очистки
            channel = await RabbitMQConnection.get_channel()

            # Удаляем очереди
            for queue_name in queue_names:
                try:
                    queue = await channel.declare_queue(queue_name, passive=True)
                    await queue.delete()
                    await asyncio.sleep(0.1)  # Даем время на обработку
                except Exception:
                    pass

            # Удаляем exchange
            for exchange_name in exchange_names:
                try:
                    exchange = await channel.get_exchange(exchange_name)
                    await exchange.delete()
                    await asyncio.sleep(0.1)
                except Exception:
                    pass

        except Exception as e:
            print(f"Cleanup warning: {e}")
        finally:
            # Всегда закрываем соединение после очистки
            try:
                await RabbitMQConnection.close()
            except Exception:
                pass

    return cleaner
