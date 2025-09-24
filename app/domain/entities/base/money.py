from dataclasses import dataclass
from enum import Enum

from domain.values.amount import AmountRUB


from enum import Enum
from dataclasses import dataclass

# TODO: Реализовать операции над деньгами


class Currency(Enum):
    """
    Перечисление поддерживаемых валют.

    Атрибуты:
        RUB (str): Российский рубль (код валюты: "RUB")

    Примеры:
        >>> Currency.RUB
        <Currency.RUB: 'RUB'>
        >>> Currency.RUB.value
        'RUB'
        >>> Currency['RUB']
        <Currency.RUB: 'RUB'>
    """

    RUB = "RUB"


@dataclass(frozen=True)
class Money:
    """
    Неизменяемый объект, представляющий денежную сумму с указанием валюты.

    Состоит из суммы (AmountRUB) и валюты (Currency). По умолчанию используется RUB.
    Объект является неизменяемым после создания.

    Атрибуты:
        amount (AmountRUB): Денежная сумма. Должна быть неотрицательной.
        currency (Currency): Валюта суммы. По умолчанию Currency.RUB.

    Примеры:
        >>> # Создание денежной суммы в рублях
        >>> money = Money(AmountRUB(100.50))
        >>> print(money.amount.value)
        100.5
        >>> print(money.currency)
        <Currency.RUB: 'RUB'>

        >>> # Создание с явным указанием валюты
        >>> money = Money(AmountRUB(500.0), Currency.RUB)
        >>> money.currency.value
        'RUB'

        >>> # Строковое представление
        >>> str(money)
        '100.50 RUB'
    """

    amount: AmountRUB
    currency: Currency = Currency.RUB

    def __str__(self) -> str:
        """
        Строковое представление денежной суммы.

        Returns:
            str: Сумма с обозначением валюты в формате "amount currency"

        Пример:
            >>> money = Money(AmountRUB(123.45))
            >>> str(money)
            '123.45 RUB'
        """
        return f"{self.amount.value:.2f} {self.currency.value}"

    def __repr__(self) -> str:
        """
        Официальное строковое представление объекта для отладки.

        Returns:
            str: Репрезентация объекта с именем класса и значениями

        Пример:
            >>> money = Money(AmountRUB(99.99), Currency.RUB)
            >>> repr(money)
            "Money(amount=AmountRUB(99.99), currency=<Currency.RUB: 'RUB'>)"
        """
        return f"Money(amount={repr(self.amount)}, currency={repr(self.currency)})"

    def as_generic_type(self) -> dict:
        """
        Возвращает значение в виде базовых типов.

        Returns:
            dict: Словарь с ключами 'amount' и 'currency'

        Пример:
            >>> money = Money(AmountRUB(250.0))
            >>> money.as_generic_type()
            {'amount': 250.0, 'currency': 'RUB'}
        """
        return {
            "amount": self.amount.as_generic_type(),
            "currency": self.currency.value,
        }

    @classmethod
    def from_float(cls, amount: float, currency: Currency = Currency.RUB) -> "Money":
        """
        Создает объект Money из числового значения.

        Args:
            amount (float): Денежная сумма
            currency (Currency): Валюта. По умолчанию Currency.RUB.

        Returns:
            Money: Новый экземпляр Money

        Вызывает:
            ValueError: Если сумма отрицательная

        Пример:
            >>> money = Money.from_float(300.75)
            >>> isinstance(money.amount, AmountRUB)
            True
            >>> money.amount.value
            300.75
        """
        return cls(AmountRUB(amount), currency)

    def is_positive(self) -> bool:
        """
        Проверяет, является ли сумма положительной.

        Returns:
            bool: True если сумма > 0, иначе False

        Пример:
            >>> Money(AmountRUB(100.0)).is_positive()
            True
            >>> Money(AmountRUB(0.0)).is_positive()
            False
        """
        return self.amount.value > 0
