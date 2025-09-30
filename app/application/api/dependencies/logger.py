from infra.config import app_logger
from logging import Logger


async def get_logger() -> Logger:
    return app_logger
