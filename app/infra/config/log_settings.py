import sys
from loguru import logger


class LoggerConfig:
    """Конфигурация логгера"""

    @staticmethod
    def configure(
        log_level: str = "INFO", debug: bool = False, log_format: str = "json"
    ) -> None:
        """Настройка логгера"""

        # Убираем стандартные handlers
        logger.remove()

        # Формат для консоли (читаемый)
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

        # Формат для файлов (JSON)
        if log_format == "json":
            file_format = (
                "{time:YYYY-MM-DD HH:mm:ss} | {level} | "
                "{module}:{function}:{line} | {message}"
            )
        else:
            file_format = console_format

        # Консольный вывод (читаемый формат)
        logger.add(
            sys.stderr,
            format=console_format,
            level=log_level,
            colorize=True,
            serialize=False,  # Не сериализуем в JSON для консоли
            backtrace=True,
            diagnose=debug,
        )

        # Файловый вывод (JSON формат)
        if not debug:
            logger.add(
                "logs/app.log",
                rotation="10 MB",
                retention="30 days",
                format=file_format,
                level=log_level,
                serialize=True,  # Сериализуем в JSON для файлов
                backtrace=True,
                diagnose=False,
            )

        # Логирование ошибок в отдельный файл (JSON формат)
        logger.add(
            "logs/error.log",
            rotation="5 MB",
            retention="15 days",
            level="ERROR",
            format=file_format,
            serialize=True,  # Сериализуем в JSON для файлов
        )


# Глобальный инстанс логгера
app_logger = logger
