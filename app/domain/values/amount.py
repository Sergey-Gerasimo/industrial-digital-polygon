from dataclasses import dataclass

from domain.values.base import BaseValueObject


@dataclass(frozen=True)
class AmountRUB(BaseValueObject):
    """
    Неизменяемый объект-значение, представляющий денежную сумму в рублях.

    Этот класс обеспечивает валидацию и безопасную работу с денежными суммами.
    Объект является неизменяемым после создания.

    Атрибуты:
        value (float): Денежная сумма в рубях. Должна быть неотрицательной.

    Вызывает:
        ValueError: Если значение суммы отрицательное

    Примеры:
        >>> # Создание валидной суммы
        >>> amount = AmountRUB(100.50)
        >>> print(amount.value)
        100.5

        >>> # Получение базового типа
        >>> amount.as_generic_type()
        100.5

        >>> # Попытка создать отрицательную сумму
        >>> try:
        ...     AmountRUB(-50.0)
        ... except ValueError as e:
        ...     print(f"Ошибка: {e}")
        Ошибка: Сумма не может быть отрицательной
    """

    value: float

    def __post_init__(self):
        """
        Автоматически валидирует сумму после инициализации.

        Этот метод вызывается dataclass после __init__ и гарантирует,
        что объект всегда находится в валидном состоянии.
        """
        self.validate()

    def validate(self):
        """
        Валидирует, что сумма является корректной.

        Проверяет:
            - Сумма не отрицательная (value >= 0)

        Вызывает:
            ValueError: Если сумма отрицательная

        Пример:
            >>> # Валидная сумма
            >>> AmountRUB(0.0)  # Не вызывает исключение
            >>> AmountRUB(500.75)  # Не вызывает исключение

            >>> # Невалидная сумма
            >>> AmountRUB(-100.0)
            ValueError: Сумма не может быть отрицательной
        """
        if self.value < 0:
            raise ValueError("Сумма не может быть отрицательной")

    def as_generic_type(self) -> float:
        """
        Возвращает значение в виде базового типа.

        Returns:
            float: Числовое представление суммы в рублях

        Пример:
            >>> amount = AmountRUB(250.30)
            >>> amount.as_generic_type()
            250.3
            >>> type(amount.as_generic_type())
            <class 'float'>
        """
        return self.value

    def __str__(self) -> str:
        """
        Строковое представление объекта.

        Returns:
            str: Сумма в рублях с обозначением валюты

        Пример:
            >>> amount = AmountRUB(123.45)
            >>> str(amount)
            '123.45 RUB'
        """
        return f"{self.value} RUB"

    def __repr__(self) -> str:
        """
        Официальное строковое представление объекта для отладки.

        Returns:
            str: Репрезентация объекта с именем класса и значением

        Пример:
            >>> amount = AmountRUB(99.99)
            >>> repr(amount)
            'AmountRUB(99.99)'
        """
        return f"AmountRUB({self.value})"
