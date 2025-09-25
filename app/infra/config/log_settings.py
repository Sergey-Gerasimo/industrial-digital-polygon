import sys
from loguru import logger


class LoggerConfig:
    """Конфигурация логгера для приложения.

    Предоставляет статический метод для настройки логгера с поддержкой
    различных форматов вывода, уровней логирования и разделения логов
    по назначению (консоль, файлы приложения, файлы ошибок).

    Attributes:
        Не содержит атрибутов, так как все методы статические.

    Example:
        >>> # Базовая настройка логгера
        >>> LoggerConfig.configure(log_level="INFO")
        >>>
        >>> # Настройка для разработки с подробным выводом
        >>> LoggerConfig.configure(log_level="DEBUG", debug=True)
        >>>
        >>> # Настройка для production с JSON форматом
        >>> LoggerConfig.configure(log_level="WARNING", log_format="json")
    """

    @staticmethod
    def configure(
        log_level: str = "INFO", debug: bool = False, log_format: str = "json"
    ) -> None:
        """Настраивает логгер с указанными параметрами.

        Создает три канала логирования:
        - Консоль: читаемый формат с цветовой разметкой
        - Файл приложения: ротация логов с сериализацией в JSON
        - Файл ошибок: отдельный файл для ошибок и критических сообщений

        Args:
            log_level: Уровень логирования. Доступные значения:
                - "TRACE" (самый подробный)
                - "DEBUG" (отладочная информация)
                - "INFO" (информационные сообщения)
                - "SUCCESS" (успешные операции)
                - "WARNING" (предупреждения)
                - "ERROR" (ошибки)
                - "CRITICAL" (критические ошибки)
            debug: Режим отладки. Если True:
                - Включает подробные traceback'и
                - Отключает файловое логирование (только консоль)
                - Использует читаемый формат для всех выводов
            log_format: Формат логирования. Доступные значения:
                - "json": Структурированный JSON формат для файлов
                - Другое значение: Читаемый текстовый формат

        Raises:
            ValueError: Если указан неподдерживаемый уровень логирования.

        Example:
            >>> # Production настройка
            >>> LoggerConfig.configure(
            ...     log_level="INFO",
            ...     debug=False,
            ...     log_format="json"
            ... )
            >>>
            >>> # Development настройка
            >>> LoggerConfig.configure(
            ...     log_level="DEBUG",
            ...     debug=True,
            ...     log_format="text"
            ... )
            >>>
            >>> # Только ошибки в production
            >>> LoggerConfig.configure(log_level="ERROR")

        Note:
            В режиме debug файловое логирование отключается для уменьшения
            нагрузки на диск во время разработки.
        """
        # Убираем стандартные handlers
        logger.remove()

        # Формат для консоли (читаемый)
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

        # Формат для файлов (JSON или текстовый)
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

        # Файловый вывод (JSON формат) - только если не в режиме debug
        if not debug:
            logger.add(
                "logs/app.log",
                rotation="10 MB",  # Ротация при достижении 10 МБ
                retention="30 days",  # Хранение логов 30 дней
                format=file_format,
                level=log_level,
                serialize=True,  # Сериализуем в JSON для файлов
                backtrace=True,
                diagnose=False,
            )

        # Логирование ошибок в отдельный файл (JSON формат)
        logger.add(
            "logs/error.log",
            rotation="5 MB",  # Ротация при достижении 5 МБ
            retention="15 days",  # Хранение ошибок 15 дней
            level="ERROR",  # Только ошибки и критические сообщения
            format=file_format,
            serialize=True,  # Сериализуем в JSON для файлов
        )

        logger.info(
            f"Logger configured successfully (level: {log_level}, debug: {debug}, format: {log_format})"
        )


# Глобальный инстанс логгера
app_logger = logger
"""Глобальный экземпляр логгера для использования во всем приложении.

Предназначен для импорта и использования в любом модуле приложения.
Уже настроен с стандартными параметрами, требует вызова LoggerConfig.configure()
для инициализации с конкретными настройками.

Example:
    >>> from infra.config import app_logger
    >>> 
    >>> # Логирование различных уровней
    >>> app_logger.debug("Отладочное сообщение")
    >>> app_logger.info("Информационное сообщение")
    >>> app_logger.warning("Предупреждение")
    >>> app_logger.error("Ошибка")
    >>> app_logger.critical("Критическая ошибка")
    >>> 
    >>> # Логирование с контекстом
    >>> app_logger.info("Пользователь вошел в систему", user_id=123, action="login")
    >>> 
    >>> # Логирование исключений
    >>> try:
    ...     risky_operation()
    ... except Exception as e:
    ...     app_logger.error("Ошибка при выполнении операции", exc_info=e)

Attributes:
    Не содержит атрибутов, так как это экземпляр логгера loguru.

Note:
    Перед использованием необходимо вызвать LoggerConfig.configure()
    для инициализации обработчиков логирования.
"""
