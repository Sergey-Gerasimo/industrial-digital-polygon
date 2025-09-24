from dataclasses import dataclass

from domain.values.base import BaseValueObject


@dataclass(frozen=True)
class UserName(BaseValueObject):
    """
    Неизменяемый объект-значение, представляющий имя пользователя.

    Этот класс предоставляет базовую обертку для имени пользователя
    с возможностью расширения валидации в будущем.

    Атрибуты:
        value (str): Имя пользователя в виде строки

    Примеры:
        >>> # Создание имени пользователя
        >>> username = UserName("john_doe")
        >>> print(username.value)
        'john_doe'

        >>> # Строковое представление
        >>> str(username)
        'john_doe'

        >>> # Репрезентация для отладки
        >>> repr(username)
        "UserName('john_doe')"

        >>> # Получение базового типа
        >>> username.as_generic_type()
        'john_doe'
    """

    value: str

    def __post_init__(self):
        """
        Автоматически валидирует username после инициализации.

        Этот метод вызывается dataclass после __init__ и гарантирует,
        что объект всегда находится в валидном состоянии.
        """
        self.validate()

    def validate(self):
        """
        Валидирует имя пользователя.

        В текущей реализации всегда возвращает True.
        Может быть расширена для добавления проверок:
            - Длина имени
            - Разрешенные символы
            - Запрещенные слова
            - Уникальность и т.д.

        Returns:
            bool: Всегда возвращает True в текущей реализации

        Пример:
            >>> username = UserName("test_user")
            >>> username.validate()
            True
        """
        return True

    def as_generic_type(self):
        """
        Возвращает значение в виде базового типа.

        Returns:
            str: Имя пользователя в виде строки

        Пример:
            >>> username = UserName("admin")
            >>> username.as_generic_type()
            'admin'
        """
        return self.value

    def __str__(self) -> str:
        """
        Строковое представление объекта.

        Returns:
            str: Имя пользователя в виде строки

        Пример:
            >>> username = UserName("alice")
            >>> str(username)
            'alice'
            >>> print(username)
            alice
        """
        return self.value

    def __repr__(self) -> str:
        """
        Официальное строковое представление объекта для отладки.

        Returns:
            str: Репрезентация объекта с именем класса и значением

        Пример:
            >>> username = UserName("bob")
            >>> repr(username)
            "UserName('bob')"
        """
        return f"UserName('{self.value}')"
