import json
import aio_pika
from infra.config import app_logger


async def simulation_consumer(message: aio_pika.IncomingMessage):
    """Обработчик для симуляции системы."""
    async with message.process():
        try:
            data = json.loads(message.body.decode())
            app_logger.info(f"Processing simulation: {data}")
            # Здесь будет логика смуляции
            # TODO: Реализовать логику смуляции с отправкой данных в другую очередь
            app_logger.info("Simulation successfully processed!")
        except Exception as e:
            app_logger.error(f"Error processing email notification: {e}")
