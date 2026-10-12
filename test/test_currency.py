import pytest

from currency_package.models import (
    FinancialEntity,
    Currency,
    Account,
    Transaction
)

from currency_package.calculations import (
    CurrencyCalculator,
    InterestCalculator
)


# Проверка создания валюты
def test_currency():
    usd = Currency("USD")

    assert usd.code == "USD"
    assert usd.rate == 90.0


# Проверка неправильной валюты
def test_invalid_currency():
    with pytest.raises(ValueError):
        Currency("GBP")


# Проверка изменения кода валюты
def test_currency_property():
    currency = Currency("USD")
    currency.code = "EUR"

    assert currency.code == "EUR"
    assert currency.rate == 100.0


# Проверка создания счёта
def test_account():
    usd = Currency("USD")
    account = Account("001", usd, 500)

    assert account.number == "001"
    assert account.balance == 500
    assert account.currency.code == "USD"


# Проверка отрицательного баланса
def test_negative_balance():
    usd = Currency("USD")

    with pytest.raises(ValueError):
        Account("001", usd, -100)


# Проверка управляемого атрибута balance
def test_balance_property():
    usd = Currency("USD")
    account = Account("001", usd, 500)

    account.balance = 1000
    assert account.balance == 1000

    with pytest.raises(ValueError):
        account.balance = -500


# Проверка отрицательной суммы операции
def test_invalid_transaction():
    usd = Currency("USD")
    rub = Currency("RUB")
    account = Account("001", usd, 500)

    with pytest.raises(ValueError):
        Transaction(account, rub, -100)


# Проверка комиссии
def test_invalid_commission():
    usd = Currency("USD")
    rub = Currency("RUB")
    account = Account("001", usd, 500)

    with pytest.raises(ValueError):
        Transaction(account, rub, 100, 150)


# Проверка изменения комиссии
def test_commission_property():
    usd = Currency("USD")
    rub = Currency("RUB")
    account = Account("001", usd, 500)
    transaction = Transaction(account, rub, 100)

    transaction.commission_percent = 5
    assert transaction.commission_percent == 5

    with pytest.raises(ValueError):
        transaction.commission_percent = -1


# Проверка конвертации валют
def test_conversion():
    usd = Currency("USD")
    rub = Currency("RUB")
    account = Account("001", usd, 500)

    transaction = Transaction(account, rub, 100, 2)

    result = CurrencyCalculator.calculate(transaction)

    assert result["converted_amount"] == 9000.0
    assert result["commission"] == 180.0
    assert result["final_amount"] == 8820.0


# Проверка конвертации без комиссии
def test_conversion_without_commission():
    usd = Currency("USD")
    eur = Currency("EUR")
    account = Account("001", usd, 500)

    transaction = Transaction(account, eur, 100, 0)

    result = CurrencyCalculator.calculate(transaction)

    assert result["converted_amount"] == 90.0
    assert result["commission"] == 0.0
    assert result["final_amount"] == 90.0


# Проверка начисления процентов
def test_interest():
    usd = Currency("USD")
    account = Account("001", usd, 500)

    result = InterestCalculator.calculate(account, 5, 30)

    assert result == 2.05


# Проверка отрицательной процентной ставки
def test_invalid_interest_rate():
    usd = Currency("USD")
    account = Account("001", usd, 500)

    with pytest.raises(ValueError):
        InterestCalculator.calculate(account, -5, 30)


# Проверка отрицательного количества дней
def test_invalid_days():
    usd = Currency("USD")
    account = Account("001", usd, 500)

    with pytest.raises(ValueError):
        InterestCalculator.calculate(account, 5, -30)


# Проверка абстрактного класса
def test_abstract_class():
    with pytest.raises(TypeError):
        FinancialEntity()


# Проверка наследования
def test_inheritance():
    usd = Currency("USD")
    account = Account("001", usd, 500)

    assert isinstance(usd, FinancialEntity)
    assert isinstance(account, FinancialEntity)


# Проверка специальных методов
def test_dunder_methods():
    usd = Currency("USD")
    account = Account("001", usd, 500)

    assert str(usd) == "USD (курс: 90.0)"
    assert repr(usd) == "Currency(code='USD')"

    assert "Счёт 001" in str(account)
    assert "Account(" in repr(account)

    assert str(CurrencyCalculator()) == "Калькулятор валют"
    assert repr(InterestCalculator()) == "InterestCalculator()"
