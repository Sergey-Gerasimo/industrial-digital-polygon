from dataclasses import dataclass
import re
from domain.values.base import BaseValueObject


@dataclass(frozen=True)
class HashedPasswordSHA256(BaseValueObject):
    """
    Неизменяемый объект-значение, представляющий хэшированный пароль SHA-256.

    Этот класс предоставляет валидацию, создание и проверку хэшей паролей SHA-256.
    Объект является неизменяемым после создания.

    Атрибуты:
        value (str): Строка хэша SHA-256 (64 шестнадцатеричных символа)

    Вызывает:
        ValueError: Если предоставленное значение не является валидным хэшем SHA-256

    Примеры:
        >>> # Создание из существующего хэша
        >>> hash_str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        >>> hashed_pw = HashedPasswordSHA256(hash_str)
        >>> print(hashed_pw.value)
        'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'

        >>> # Создание из plain password
        >>> hashed_pw = HashedPasswordSHA256.from_plain_password("мойсекретныйпароль123")
        >>> hashed_pw.verify("мойсекретныйпароль123")
        True

        >>> # Невалидный хэш вызовет исключение
        >>> try:
        ...     HashedPasswordSHA256("невалидный")
        ... except ValueError as e:
        ...     print(f"Ошибка: {e}")
        Ошибка: Неверный формат SHA-256 хэша. Должен быть ровно 64 шестнадцатеричных символа
    """

    value: str

    def __post_init__(self):
        """
        Автоматически валидирует хэш после инициализации.

        Этот метод вызывается dataclass после __init__ и гарантирует,
        что объект всегда находится в валидном состоянии.
        """
        self.validate()

    def validate(self):
        """
        Валидирует, что значение является корректным SHA-256 хэшем.

        Проверяет:
            - Тип данных (должен быть str)
            - Не пустая строка
            - Длина 64 символа
            - Шестнадцатеричный формат (0-9, a-f, A-F)

        Вызывает:
            ValueError: Если любая из проверок не проходит

        Пример:
            >>> # Валидный хэш
            >>> valid_hash = "a" * 64
            >>> HashedPasswordSHA256(valid_hash)  # Не вызывает исключение

            >>> # Невалидный хэш
            >>> HashedPasswordSHA256("короткий")
            ValueError: Неверный формат SHA-256 хэша...
        """
        if not isinstance(self.value, str):
            raise ValueError("Hashed password must be a string")

        if len(self.value) == 0:
            raise ValueError("Hashed password cannot be empty")

        # Проверка формата SHA-256
        # SHA-256 хэш должен быть 64 символа в hex формате
        sha256_pattern = r"^[a-fA-F0-9]{64}$"

        if not re.match(sha256_pattern, self.value):
            raise ValueError(
                "Invalid SHA-256 hash format. "
                "Must be exactly 64 hexadecimal characters"
            )

    def as_generic_type(self):
        """
        Возвращает значение в виде базового типа.

        Возвращает:
            str: Строковое представление хэша

        Пример:
            >>> hash_obj = HashedPasswordSHA256("a" * 64)
            >>> hash_obj.as_generic_type()
            'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        """
        return self.value

    def verify(self, plain_password: str) -> bool:
        """
        Проверяет, соответствует ли plain password этому хэшу.

        Args:
            plain_password (str): Пароль в открытом виде для проверки

        Returns:
            bool: True если пароль соответствует хэшу, иначе False

        Пример:
            >>> hash_obj = HashedPasswordSHA256.from_plain_password("пароль123")
            >>> hash_obj.verify("пароль123")
            True
            >>> hash_obj.verify("неверныйпароль")
            False
        """
        import hashlib

        hashed_input = hashlib.sha256(plain_password.encode()).hexdigest()
        return hashed_input == self.value

    @classmethod
    def from_plain_password(cls, plain_password: str) -> "HashedPasswordSHA256":
        """
        Создает хэшированный пароль из пароля в открытом виде.

        Args:
            plain_password (str): Пароль в открытом виде для хэширования

        Returns:
            HashedPasswordSHA256: Новый экземпляр с хэшированным паролем

        Вызывает:
            ValueError: Если пароль пустой или короче 4 символов

        Пример:
            >>> hashed_pw = HashedPasswordSHA256.from_plain_password("strongpassword")
            >>> isinstance(hashed_pw, HashedPasswordSHA256)
            True
            >>> len(hashed_pw.value)
            64
        """
        import hashlib

        if not plain_password:
            raise ValueError("Password cannot be empty")
        if len(plain_password) < 4:
            raise ValueError("Password must be at least 4 characters long")

        hashed = hashlib.sha256(plain_password.encode()).hexdigest()
        return cls(hashed)

    def __str__(self) -> str:
        """
        Строковое представление объекта.

        Returns:
            str: SHA-256 хэш в виде строки
        """
        return self.value

    def __repr__(self) -> str:
        """
        Официальное строковое представление объекта.

        Returns:
            str: Репрезентация объекта для отладки
        """
        return f"HashedPasswordSHA256('{self.value}')"
