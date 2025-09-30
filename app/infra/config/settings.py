from pydantic import Field, model_validator
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseSettingsWithValidation(BaseSettings):
    """Базовый класс для настроек с валидацией значений по умолчанию.

    Предоставляет метод для проверки использования значений по умолчанию
    и вывода предупреждений в лог или консоль.

    Attributes:
        model_config: Конфигурация Pydantic для загрузки из переменных окружения.
    """

    def validate_default_values(self, logger=None):
        """Проверяет использование значений по умолчанию и выводит предупреждения.

        Итерируется по всем полям модели и проверяет, совпадают ли текущие значения
        со значениями по умолчанию. Если да, выводит предупреждение с рекомендацией
        установить соответствующую переменную окружения.

        Args:
            logger: Опциональный логгер для вывода предупреждений. Если не указан,
                   используется print.

        Returns:
            self: Экземпляр класса для цепочки вызовов.

        Example:
            >>> settings = SecuritySettings()
            >>> settings.validate_default_values()
            WARNING: Настройка SecuritySettings.secret_key использует значение по умолчанию...
        """
        class_name = self.__class__.__name__

        for field_name, field_info in self.__class__.model_fields.items():
            current_value = getattr(self, field_name)

            # Получаем значение по умолчанию из Field
            default_value = field_info.default

            # Если значение совпадает с default и default не None
            if current_value == default_value and default_value is not None:
                # Получаем имя переменной окружения
                env_var_name = getattr(field_info, "alias", field_name.upper())

                # Для вложенных классов добавляем префикс из model_config
                if hasattr(self, "model_config") and hasattr(
                    self.model_config, "env_prefix"
                ):
                    prefix = self.model_config.env_prefix
                    if prefix and not env_var_name.startswith(prefix):
                        env_var_name = f"{prefix}{env_var_name}"

                warning_msg = (
                    f"Настройка {class_name}.{field_name} использует значение по умолчанию: {default_value}. "
                    f"Рекомендуется установить переменную окружения {env_var_name}"
                )

                if logger:
                    logger.warning(warning_msg)
                else:
                    print(f"WARNING: {warning_msg}")

        return self


class SuperUserSettings(BaseSettingsWithValidation):
    """Настройки суперпользователя."""

    model_config = SettingsConfigDict(env_prefix="")
    username: str = Field(default="superuser", alias="SUPERUSER_USERNAME")
    password: str = Field(default="superuser", alias="SUPERUSER_PASSWORD")


class SecuritySettings(BaseSettingsWithValidation):
    """Настройки безопасности приложения.

    Содержит параметры для JWT токенов и шифрования.

    Attributes:
        secret_key (str): Секретный ключ для подписи JWT токенов.
        algorithm (str): Алгоритм шифрования JWT токенов.
        access_token_expire_minutes (int): Время жизни access токена в минутах.

    Example:
        >>> security = SecuritySettings()
        >>> print(security.secret_key)
        'your-secret-key-change-this-in-production'
    """

    model_config = SettingsConfigDict(env_prefix="")

    secret_key: str = Field(
        default="your-secret-key-change-this-in-production", alias="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_minutes: int = Field(
        default=7 * 24 * 60, alias="REFRESH_TOKEN_EXPIRE_MINUTES"
    )

    def validate_default_values(self, logger=None):
        """Специфичная валидация для настроек безопасности.

        Особое внимание уделяется проверке секретного ключа, так как использование
        значения по умолчанию в продакшене представляет угрозу безопасности.

        Args:
            logger: Опциональный логгер для вывода предупреждений.

        Returns:
            self: Экземпляр класса для цепочки вызовов.
        """
        if self.secret_key == "your-secret-key-change-this-in-production":
            warning_msg = (
                "Настройка SecuritySettings.secret_key использует значение по умолчанию. "
                "Это небезопасно для продакшн окружения. "
                "Рекомендуется установить переменную окружения SECRET_KEY"
            )
            if logger:
                logger.warning(warning_msg)
            else:
                print(f"WARNING: {warning_msg}")


class LogSettings(BaseSettingsWithValidation):
    """Настройки логирования приложения.

    Определяет уровень детализации логов, формат и режим отладки.

    Attributes:
        debug (bool): Режим отладки (True/False).
        log_level (str): Уровень логирования (DEBUG, INFO, WARNING, ERROR).
        log_format (str): Формат логов (json, text).
    """

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    def validate_default_values(self, logger=None):
        """Валидация настроек логирования для продакшн окружения.

        Проверяет, что debug режим выключен и установлен адекватный уровень логирования.

        Args:
            logger: Опциональный логгер для вывода предупреждений.

        Returns:
            self: Экземпляр класса для цепочки вызовов.
        """
        if self.debug:
            warning_msg = (
                "Настройка LogSettings.debug установлена в True. "
                "Это небезопасно для продакшн окружения. "
                "Рекомендуется установить переменную окружения DEBUG в False"
            )
            if logger:
                logger.warning(warning_msg)
            else:
                print(f"WARNING: {warning_msg}")

        if self.log_level == "INFO":
            warning_msg = (
                "Настройка LogSettings.log_level использует значение по умолчанию 'INFO'. "
                "Рекомендуется установить переменную окружения LOG_LEVEL в 'WARNING' или 'ERROR' для продакшн окружения"
            )
            if logger:
                logger.warning(warning_msg)
            else:
                print(f"WARNING: {warning_msg}")

        return super().validate_default_values(logger=logger)


class RedisSettings(BaseSettingsWithValidation):
    """Настройки подключения к Redis.

    Содержит параметры для подключения и настройки пула соединений с Redis.

    Attributes:
        host (str): Хост Redis сервера.
        port (int): Порт Redis сервера.
        db (int): Номер базы данных Redis.
        max_connections (int): Максимальное количество соединений в пуле.
        decode_responses (bool): Декодировать ответы из bytes в str.
        password (Optional[str]): Пароль для аутентификации в Redis.
        default_timeout (int): Таймаут по умолчанию для операций.

    Properties:
        url (str): URL для подключения к Redis.
    """

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="PORT")
    db: int = Field(default=0, alias="REDIS_DB")
    max_connections: int = Field(default=10, alias="REDIS_MAX_CONNECTIONS")
    decode_responses: bool = Field(default=True, alias="REDIS_DECODE_RESPONSES")
    password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    default_timeout: int = Field(default=300, alias="REDIS_DEFAULT_TIMEOUT")

    @property
    def url(self) -> str:
        """Генерирует URL для подключения к Redis.

        Returns:
            str: Redis URL в формате redis://[user:password@]host:port/db

        Example:
            >>> redis = RedisSettings()
            >>> print(redis.url)
            'redis://localhost:6379/0'
        """
        if self.password is None:
            return f"redis://{self.host}:{self.port}/{self.db}"

        return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"


class DatabaseSettings(BaseSettingsWithValidation):
    """Настройки подключения к PostgreSQL базе данных.

    Содержит параметры для подключения и настройки пула соединений с PostgreSQL.

    Attributes:
        db (str): Имя базы данных.
        user (str): Имя пользователя базы данных.
        password (str): Пароль пользователя.
        host (str): Хост базы данных.
        port (int): Порт базы данных.
        pool_size (int): Размер пула соединений.
        max_overflow (int): Максимальное количество соединений сверх pool_size.
        echo (bool): Логировать SQL запросы.

    Properties:
        url_asyncpg (str): URL для подключения через asyncpg.
        url (str): Стандартный URL для подключения.
    """

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    db: str = Field(default="postgres", alias="POSTGRES_DB")
    user: str = Field(default="postgres", alias="POSTGRES_USER")
    password: str = Field(default="password", alias="POSTGRES_PASSWORD")
    host: str = Field(default="localhost", alias="POSTGRES_HOST")
    port: int = Field(default=5432, alias="POSTGRES_PORT")
    pool_size: int = Field(default=10, alias="POSTGRES_POOL_SIZE")
    max_overflow: int = Field(default=20, alias="POSTGRES_MAX_OVERFLOW")
    echo: bool = Field(default=False, alias="POSTGRES_ECHO")

    @property
    def url_asyncpg(self) -> str:
        """Генерирует URL для подключения к PostgreSQL через asyncpg.

        Returns:
            str: PostgreSQL URL в формате postgresql+asyncpg://user:password@host:port/db

        Example:
            >>> db = DatabaseSettings()
            >>> print(db.url_asyncpg)
            'postgresql+asyncpg://postgres:password@localhost:5432/postgres'
        """
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    def url(self) -> str:
        """Генерирует стандартный URL для подключения к PostgreSQL.

        Returns:
            str: PostgreSQL URL в формате postgresql://user:password@host:port/db
        """
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class APISettings(BaseSettingsWithValidation):
    """Настройки API сервера.

    Определяет параметры запуска и конфигурации HTTP сервера.

    Attributes:
        port (int): Порт для запуска сервера.
        host (str): Хост для запуска сервера.
        reload (bool): Автоматическая перезагрузка при изменении кода.
        allowed_hosts (List[str]): Список разрешенных хостов.
    """

    model_config = SettingsConfigDict(env_prefix="API_")

    port: int = Field(default=8080, alias="API_PORT")
    host: str = Field(default="0.0.0.0", alias="API_HOST")
    reload: bool = Field(default=True, alias="API_RELOAD")
    allowed_hosts: List[str] = Field(default=["*"], alias="API_ALLOWED_HOSTS")

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        """Валидатор для парсинга списка хостов из строки.

        Позволяет указывать хосты через запятую в переменной окружения.

        Args:
            v: Значение для валидации (str или list).

        Returns:
            List[str]: Список хостов.

        Example:
            >>> APISettings.parse_allowed_hosts("localhost,127.0.0.1")
            ['localhost', '127.0.0.1']
        """
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v


class RabbitMQSettings(BaseSettingsWithValidation):
    """Настройки подключения к RabbitMQ.

    Содержит параметры для подключения к брокеру сообщений RabbitMQ.

    Attributes:
        host (str): Хост RabbitMQ сервера.
        user (str): Имя пользователя RabbitMQ.
        password (str): Пароль пользователя.
        timeout (int): Таймаут подключения.
        max_connections (int): Максимальное количество соединений.
        port (int): Порт RabbitMQ сервера.
        management_port (int): Порт веб-интерфейса управления.
        default_queue (str): Имя очереди по умолчанию.

    Properties:
        url (str): URL для подключения к RabbitMQ.
    """

    model_config = SettingsConfigDict(env_prefix="RABBITMQ_")

    host: str = Field(default="localhost", alias="RABBITMQ_HOST")
    user: str = Field(default="rabbitmq_user", alias="RABBITMQ_USER")
    password: str = Field(default="rabbitmq_password", alias="RABBITMQ_PASSWORD")
    timeout: int = Field(default=5, alias="RABBITMQ_TIMEOUT")
    max_connections: int = Field(default=10, alias="RABBITMQ_MAX_CONNECTIONS")
    port: int = Field(default=5672, alias="RABBITMQ_PORT")
    management_port: int = Field(
        default=15672, alias="RABBITMQ_RABBITMQ_MANAGEMENT_PORT"
    )
    default_queue: str = Field(default="default", alias="RABBITMQ_DEFAULT_QUEUE")

    @property
    def url(self) -> str:
        """Генерирует URL для подключения к RabbitMQ.

        Returns:
            str: RabbitMQ URL в формате amqp://user:password@host:port//

        Example:
            >>> rabbit = RabbitMQSettings()
            >>> print(rabbit.url)
            'amqp://rabbitmq_user:rabbitmq_password@localhost:5672//'
        """
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}//"


class Settings(BaseSettingsWithValidation):
    """Главный класс настроек приложения.

    Объединяет все группы настроек в единую конфигурацию.

    Attributes:
        pythonpath (str): Путь к Python приложению.
        secrurity (SecuritySettings): Настройки безопасности.
        log (LogSettings): Настройки логирования.
        api (APISettings): Настройки API.
        postgres (DatabaseSettings): Настройки базы данных.
        redis (RedisSettings): Настройки Redis.
        rabbitmq (RabbitMQSettings): Настройки RabbitMQ.
    """

    pythonpath: str = Field(default="app", alias="PYTHONPATH")

    secrurity: SecuritySettings = Field(default_factory=SecuritySettings)
    log: LogSettings = Field(default_factory=LogSettings)
    api: APISettings = Field(default_factory=APISettings)
    postgres: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)

    def validate_default_values(self, logger=None):
        """Рекурсивная валидация всех вложенных настроек.

        Вызывает validate_default_values для всех дочерних классов настроек.

        Args:
            logger: Опциональный логгер для вывода предупреждений.

        Returns:
            self: Экземпляр класса для цепочки вызовов.
        """
        super().validate_default_values(logger=logger)
        self.log.validate_default_values(logger=logger)
        self.api.validate_default_values(logger=logger)
        self.postgres.validate_default_values(logger=logger)
        self.redis.validate_default_values(logger=logger)
        self.rabbitmq.validate_default_values(logger=logger)
        self.secrurity.validate_default_values(logger=logger)
        return self

    def __str__(self):
        return (
            "API\n"
            "   host: {self.api.host}\n"
            "   port: {self.api.port}\n"
            "   reload: {self.api.reload}\n"
            "   allowed_hosts: {self.api.allowed_hosts}\n"
            "PostgreSQL\n"
            "   host: {self.postgres.host}\n"
            "   port: {self.postgres.port}\n"
            "   db: {self.postgres.db}\n"
            "   user: {self.postgres.user}\n"
            "   password: {self.postgres.password}\n"
            "   pool_size: {self.postgres.pool_size}\n"
            "   max_overflow: {self.postgres.max_overflow}\n"
            "   echo: {self.postgres.echo}\n"
            "Redis\n"
            "   host: {self.redis.host}\n"
            "   port: {self.redis.port}\n"
            "   password: {self.redis.password}\n"
            "   default_timeout: {self.redis.default_timeout}\n"
            "   db: {self.redis.db}\n"
            "   max_connections: {self.redis.max_connections}\n"
            "   decode_responses: {self.redis.decode_responses}\n"
            "RabbitMQ\n"
            "   host: {self.rabbitmq.host}\n"
            "   port: {self.rabbitmq.port}\n"
            "   management_port: {self.rabbitmq.management_port}\n"
            "   user: {self.rabbitmq.user}\n"
            "   password: {self.rabbitmq.password}\n"
            "   default_queue: {self.rabbitmq.default_queue}\n"
        ).format(self=self)


settings = Settings()
"""Глобальный экземпляр настроек приложения.

Используется для доступа к настройкам из любого модуля приложения.

Example:
    >>> from settings import settings
    >>> print(settings.api.port)
    8080
    >>> print(settings.postgres.url_asyncpg)
    'postgresql+asyncpg://postgres:password@localhost:5432/postgres'
"""
