
class Currency:
    RATES = {
        "RUB": 1.0,
        "USD": 90.0,
        "EUR": 100.0
    }

    def __init__(self, code):
        code = code.upper()

        if code not in self.RATES:
            raise ValueError("Неизвестная валюта")

        self.code = code
        self.rate = self.RATES[code]

    def __str__(self):
        return f"{self.code} (курс: {self.rate})"

    def __repr__(self):
        return f"Currency(code='{self.code}')"


class Account:
    def __init__(self, number, currency, balance=0):
        if balance < 0:
            raise ValueError("Баланс не может быть отрицательным")

        self.number = number
        self.currency = currency
        self.balance = balance

    def __str__(self):
        return f"Счёт {self.number}: {self.balance} {self.currency.code}"

    def __repr__(self):
        return f"Account(number='{self.number}', balance={self.balance})"


class Transaction:
    def __init__(self, account, target_currency, amount, commission_percent=2):
        if amount <= 0:
            raise ValueError("Сумма операции должна быть положительной")

        if not 0 <= commission_percent <= 100:
            raise ValueError("Некорректная комиссия")

        self.account = account
        self.target_currency = target_currency
        self.amount = amount
        self.commission_percent = commission_percent

    def __str__(self):
        return (
            f"Обмен {self.amount} {self.account.currency.code} "
            f"на {self.target_currency.code}"
        )

    def __repr__(self):
        return f"Transaction(amount={self.amount})"
