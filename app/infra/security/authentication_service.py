"""
Сервис аутентификации по паролю.

Этот модуль предоставляет простой сервис для хэширования и проверки паролей на
основе value-object `HashedPasswordSHA256`, который хранит SHA-256 хэш
фиксированной длины (64 шестнадцатеричных символа).

Пример:
    Хеширование и проверка пароля::

        service = PasswordAuthenticationService()
        hashed = service.hash_password("myStrongPassword123!")
        assert service.verify_password("myStrongPassword123!", hashed) is True
        assert service.verify_password("wrong", hashed) is False
"""

from domain.values.hashed_password import HashedPasswordSHA256


class PasswordAuthenticationService:
    """Сервис работы с паролями (хеширование и проверка) через SHA-256 value-object."""

    def hash_password(self, plain_password: str) -> HashedPasswordSHA256:
        """Вычисляет SHA-256 хэш пароля и возвращает value-object.

        Args:
            plain_password: Пароль в открытом виде для хеширования.

        Returns:
            HashedPasswordSHA256: Объект с валидированным SHA-256 хэшем
        """
        return HashedPasswordSHA256.from_plain_password(plain_password)

    def verify_password(
        self, plain_password: str, hashed_password: HashedPasswordSHA256
    ) -> bool:
        """Проверяет соответствие пароля его SHA-256 хэшу.

        Args:
            plain_password: Пароль в открытом виде, введённый пользователем.
            hashed_password: Объект-значение с ранее сохранённым хэшем пароля.

        Returns:
            bool: True, если пароль корректен, иначе False.
        """
        return hashed_password.verify(plain_password)
