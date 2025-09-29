"""
Пакет средств безопасности приложения.

Содержит инструменты для работы с аутентификацией и авторизацией, включая
обработчик JWT и сервис проверки/хеширования паролей.

Пример:
    Импорт и использование::

        from infra.security import JWTHandler, PasswordAuthenticationService

        jwt = JWTHandler(secret="secret", algorithm="HS256")
        auth = PasswordAuthenticationService()
        hashed = auth.hash_password("strongPass!42")
        assert auth.verify_password("strongPass!42", hashed)
"""

from .jwt_handler import JWTHandler
from .authentication_service import PasswordAuthenticationService

__all__ = [
    "JWTHandler",
    "PasswordAuthenticationService",
]
