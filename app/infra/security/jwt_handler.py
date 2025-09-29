import datetime
from typing import Any, Union
from jose import JWTError, jwt
from infra.config import settings
from infra.config import app_logger


class JWTHandler:
    """
    Обработчик JWT токенов для аутентификации и авторизации.

    Класс предоставляет методы для создания и верификации access и refresh токенов
    с использованием библиотеки python-jose.

    Attributes:
        expire (int): Время жизни access токена в минутах
        refresh_expire (int): Время жизни refresh токена в минутах
        algorithm (str): Алгоритм шифрования (например, HS256)
        secret (str): Секретный ключ для подписи токенов

    Example:
        >>> from infra.config import settings
        >>> jwt_handler = JWTHandler()
        >>>
        >>> # Создание access токена
        >>> access_token = jwt_handler.create_access_token("user123")
        >>> print(f"Access token: {access_token}")
        >>>
        >>> # Создание refresh токена
        >>> refresh_token = jwt_handler.create_refresh_token("user123")
        >>> print(f"Refresh token: {refresh_token}")
        >>>
        >>> # Верификация токена
        >>> payload = jwt_handler.veryfi_token(access_token)
        >>> if payload:
        >>>     print(f"Данные токена: {payload}")
        >>> else:
        >>>     print("Неверный токен")
    """

    def __init__(
        self,
        access_token_expire_minutes: int,
        refresh_token_expire_minutes: int,
        secret_key: str,
        algorithm: str,
    ):
        """
        Инициализация обработчика JWT токенов.

        Args:
            access_token_expire_minutes: Время жизни access токена в минутах
            refresh_token_expire_minutes: Время жизни refresh токена в минутах
            secret_key: Секретный ключ для подписи токенов
            algorithm: Алгоритм шифрования

        Example:
            >>> # С настройками по умолчанию из конфигурации
            >>> handler = JWTHandler()
            >>>
            >>> # С кастомными настройками
            >>> custom_handler = JWTHandler(
            >>>     access_token_expire_minutes=60,
            >>>     refresh_token_expire_minutes=1440,
            >>>     secret_key="my-secret-key",
            >>>     algorithm="HS256"
            >>> )
        """
        self.expire = access_token_expire_minutes
        self.refresh_expire = refresh_token_expire_minutes
        self.algorithm = algorithm
        self.secret_key = secret_key

    def _create_token(self, subject: str, expires_in_minutes: int) -> str:
        """
        Внутренняя функция для создания JWT токена.

        Args:
            subject: Субъект токена (идентификатор пользователя).
            expires_in_minutes: Срок жизни токена в минутах.

        Returns:
            Encoded JWT токен.
        """
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        expiration_time = now + datetime.timedelta(minutes=expires_in_minutes)
        payload = {"exp": expiration_time, "sub": subject}
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_access_token(self, subject: str, expires_delta: int = None):
        """
        Создает JWT access токен для указанного субъекта.

        Access токен используется для аутентификации запросов и имеет
        ограниченное время жизни.

        Args:
            subject: Идентификатор субъекта (обычно user_id или username)
            expires_delta: Кастомное время жизни токена в минутах.
                          Если None, используется значение из конфигурации.

        Returns:
            str: Закодированный JWT токен

        Raises:
            JWTError: Если произошла ошибка при кодировании токена

        Example:
            >>> jwt_handler = JWTHandler()
            >>>
            >>> # Создание токена с временем по умолчанию
            >>> token1 = jwt_handler.create_access_token("user_123")
            >>>
            >>> # Создание токена с кастомным временем жизни (30 минут)
            >>> token2 = jwt_handler.create_access_token("user_123", expires_delta=30)
            >>>
            >>> # Создание токена для объекта пользователя
            >>> user = {"id": 1, "username": "john_doe"}
            >>> token3 = jwt_handler.create_access_token(user["id"])
        """
        if expires_delta is None:
            expires_delta = self.expire

        return self._create_token(subject, expires_delta)

    def create_refresh_token(
        self, subject: Union[str, Any], expires_delta: int = None
    ) -> str:
        """
        Создает JWT refresh токен для указанного субъекта.

        Refresh токен используется для получения нового access токена
        и имеет более длительное время жизни.

        Args:
            subject: Идентификатор субъекта (обычно user_id или username)
            expires_delta: Кастомное время жизни токена в минутах.
                          Если None, используется значение из конфигурации.

        Returns:
            str: Закодированный JWT refresh токен

        Raises:
            JWTError: Если произошла ошибка при кодировании токена

        Example:
            >>> jwt_handler = JWTHandler()
            >>>
            >>> # Создание refresh токена
            >>> refresh_token = jwt_handler.create_refresh_token("user_123")
            >>>
            >>> # Использование refresh токена для получения нового access токена
            >>> # (в реальном сценарии это будет отдельный endpoint)
            >>> payload = jwt_handler.veryfi_token(refresh_token)
            >>> if payload and payload.get("sub"):
            >>>     new_access_token = jwt_handler.create_access_token(payload["sub"])
        """
        if expires_delta is None:
            expires_delta = self.expire

        return self._create_token(subject, expires_delta)

    def verify_token(self, token: str) -> Union[dict, None]:
        """
        Проверяет и декодирует JWT токен.

        Args:
            token: JWT токен для верификации

        Returns:
            Union[dict, None]: Полезная нагрузка токена в случае успеха,
                             None если токен невалидный или просроченный

        Example:
            >>> jwt_handler = JWTHandler()
            >>> token = jwt_handler.create_access_token("user_123")
            >>>
            >>> # Успешная верификация
            >>> payload = jwt_handler.veryfi_token(token)
            >>> if payload:
            >>>     user_id = payload.get("sub")
            >>>     exp_date = payload.get("exp")
            >>>     print(f"User: {user_id}, Expires: {exp_date}")
            >>>
            >>> # Неудачная верификация (просроченный токен)
            >>> expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            >>> payload = jwt_handler.veryfi_token(expired_token)
            >>> if payload is None:
            >>>     print("Токен невалиден или просрочен")
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
