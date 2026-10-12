from abc import ABC, abstractmethod


# Абстрактный базовый класс
class FinancialEntity(ABC):

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def __repr__(self):
        pass


# Класс валюты
class Currency(FinancialEntity):

    RATES = {
        "RUB": 1.0,
        "USD": 90.0,
        "EUR": 100.0
    }

    def __init__(self, code):
        self.code = code

    # Управляемый атрибут code
    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, value):
        value = value.upper()

        if value not in self.RATES:
            raise ValueError("Неизвестная валюта")

        self._code = value

    # Курс доступен только для чтения
    @property
    def rate(self):
        return self.RATES[self.code]

    def __str__(self):
        return f"{self.code} (курс: {self.rate})"

    def __repr__(self):
        return f"Currency(code='{self.code}')"


# Класс банковского счёта
class Account(FinancialEntity):

    def __init__(self, number, currency, balance=0):
        self.number = number
        self.currency = currency
        self.balance = balance

    # Управляемый атрибут balance
    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        if value < 0:
            raise ValueError(
                "Баланс не может быть отрицательным"
            )

        self._balance = value

    def __str__(self):
        return (
            f"Счёт {self.number}: "
            f"{self.balance} {self.currency.code}"
        )

    def __repr__(self):
        return (
            f"Account(number='{self.number}', "
            f"balance={self.balance})"
        )


# Класс транзакции
class Transaction(FinancialEntity):

    def __init__(
        self,
        account,
        target_currency,
        amount,
        commission_percent=2
    ):
        self.account = account
        self.target_currency = target_currency
        self.amount = amount
        self.commission_percent = commission_percent

    # Управляемый атрибут amount
    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, value):
        if value <= 0:
            raise ValueError(
                "Сумма операции должна быть положительной"
            )

        self._amount = value

    # Управляемый атрибут commission_percent
    @property
    def commission_percent(self):
        return self._commission_percent

    @commission_percent.setter
    def commission_percent(self, value):
        if not 0 <= value <= 100:
            raise ValueError("Некорректная комиссия")

        self._commission_percent = value

    def __str__(self):
        return (
            f"Обмен {self.amount} "
            f"{self.account.currency.code} "
            f"на {self.target_currency.code}"
        )

    def __repr__(self):
        return f"Transaction(amount={self.amount})"
