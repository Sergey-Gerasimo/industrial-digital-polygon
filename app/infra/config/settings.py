from pydantic import Field, model_validator
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseSettingsWithValidation(BaseSettings):
    def validate_default_values(self, logger=None):
        """Проверяет, используются ли значения по умолчанию и выводит предупреждения"""
        class_name = self.__class__.__name__

        for field_name, field_info in self.model_fields.items():
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


class LogSettings(BaseSettingsWithValidation):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")


class RedisSettings(BaseSettingsWithValidation):
    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="PORT")
    password: str = Field(default="redis123", alias="REDIS_PASSWORD")
    default_timeout: int = Field(default=300, alias="REDIS_DEFAULT_TIMEOUT")


class DatabaseSettings(BaseSettingsWithValidation):
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
    def url(self) -> str:
        """URL для подключения к PostgreSQL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class APISettings(BaseSettingsWithValidation):
    model_config = SettingsConfigDict(env_prefix="API_")

    port: int = Field(default=8080, alias="API_PORT")
    host: str = Field(default="0.0.0.0", alias="API_HOST")
    reload: bool = Field(default=True, alias="API_RELOAD")
    allowed_hosts: List[str] = Field(default=["*"], alias="API_ALLOWED_HOSTS")

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v


class RabbitMQSettings(BaseSettingsWithValidation):
    model_config = SettingsConfigDict(env_prefix="RABBITMQ_")

    host: str = Field(default="localhost", alias="RABBITMQ_HOST")
    user: str = Field(default="rabbitmq_user", alias="RABBITMQ_USER")
    password: str = Field(default="rabbitmq_password", alias="RABBITMQ_PASSWORD")
    port: int = Field(default=5672, alias="RABBITMQ_PORT")
    management_port: int = Field(
        default=15672, alias="RABBITMQ_RABBITMQ_MANAGEMENT_PORT"
    )
    default_queue: str = Field(default="default", alias="RABBITMQ_DEFAULT_QUEUE")

    @property
    def url(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}//"


class Settings(BaseSettingsWithValidation):
    pythonpath: str = Field(default="app", alias="PYTHONPATH")

    log: LogSettings = Field(default_factory=LogSettings)
    api: APISettings = Field(default_factory=APISettings)
    postgres: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)

    def validate_default_values(self, logger=None):
        super().validate_default_values(logger=logger)
        self.log.validate_default_values(logger=logger)
        self.api.validate_default_values(logger=logger)
        self.postgres.validate_default_values(logger=logger)
        self.redis.validate_default_values(logger=logger)
        self.rabbitmq.validate_default_values(logger=logger)
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
            "RabbitMQ\n"
            "   host: {self.rabbitmq.host}\n"
            "   port: {self.rabbitmq.port}\n"
            "   management_port: {self.rabbitmq.management_port}\n"
            "   user: {self.rabbitmq.user}\n"
            "   password: {self.rabbitmq.password}\n"
            "   default_queue: {self.rabbitmq.default_queue}\n"
        ).format(self=self)


settings = Settings()
