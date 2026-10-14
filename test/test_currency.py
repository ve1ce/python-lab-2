import pytest

from currency_package.models import FinancialEntity, Currency, Account, Transaction
from currency_package.calculations import CurrencyCalculator, InterestCalculator


# Создание валюты и изменение её кода через property.
def test_currency():
    currency = Currency("USD")
    assert currency.code == "USD"
    assert currency.rate == 90.0

    currency.code = "EUR"
    assert currency.rate == 100.0

    with pytest.raises(ValueError):
        Currency("AUD")


# Проверяем курсы остальных доступных валют.
def test_other_currencies():
    rates = {"GBP": 115.0, "CNY": 12.5, "JPY": 0.6, "CHF": 105.0}
    for code, rate in rates.items():
        assert Currency(code).rate == rate


# Создание счёта и проверка изменения баланса.
def test_account():
    account = Account("001", Currency("USD"), 500)
    assert account.number == "001"
    assert account.currency.code == "USD"
    assert account.balance == 500

    account.balance = 1000
    assert account.balance == 1000

    with pytest.raises(ValueError):
        account.balance = -100
    with pytest.raises(ValueError):
        Account("002", Currency("USD"), -100)


# Транзакция округляет сумму и проверяет комиссию.
def test_transaction():
    account = Account("001", Currency("USD"), 500)
    transaction = Transaction(account, Currency("EUR"), 100.567, 2)

    assert transaction.amount == 100.57
    transaction.commission_percent = 5
    assert transaction.commission_percent == 5

    with pytest.raises(ValueError):
        transaction.commission_percent = -1


# Недопустимые суммы и проценты комиссии.
def test_invalid_transaction():
    account = Account("001", Currency("USD"), 500)
    eur = Currency("EUR")

    for amount in (-100, 0.001, float("nan")):
        with pytest.raises(ValueError):
            Transaction(account, eur, amount)

    for commission in (150, float("inf")):
        with pytest.raises(ValueError):
            Transaction(account, eur, 100, commission)


# Конвертация: курс, комиссия и итоговая сумма.
def test_conversion():
    account = Account("001", Currency("USD"), 500)

    result = CurrencyCalculator.calculate(
        Transaction(account, Currency("RUB"), 100, 2)
    )
    assert result["converted_amount"] == 9000.0
    assert result["commission"] == 180.0
    assert result["final_amount"] == 8820.0

    result = CurrencyCalculator.calculate(
        Transaction(account, Currency("EUR"), 100, 2)
    )
    assert result["exchange_rate"] == pytest.approx(0.9)
    assert result["final_amount"] == 88.2

    result = CurrencyCalculator.calculate(
        Transaction(account, Currency("EUR"), 100, 0)
    )
    assert result["commission"] == 0
    assert result["final_amount"] == 90.0


# Расчёт процентов не изменяет баланс счёта.
def test_interest():
    account = Account("001", Currency("USD"), 500)
    assert InterestCalculator.calculate(account, 5, 30) == 2.05
    assert account.balance == 500


# Ошибки в процентной ставке и количестве дней.
def test_invalid_interest():
    account = Account("001", Currency("USD"), 500)
    with pytest.raises(ValueError):
        InterestCalculator.calculate(account, -5, 30)
    with pytest.raises(ValueError):
        InterestCalculator.calculate(account, 5, -30)


# Абстрактный класс нельзя создать напрямую, от него наследуются модели.
def test_inheritance():
    with pytest.raises(TypeError):
        FinancialEntity()

    account = Account("001", Currency("USD"), 500)
    transaction = Transaction(account, Currency("EUR"), 100)
    assert isinstance(account.currency, FinancialEntity)
    assert isinstance(account, FinancialEntity)
    assert isinstance(transaction, FinancialEntity)


# Специальные методы строкового представления объектов.
def test_dunder_methods():
    currency = Currency("USD")
    account = Account("001", currency, 500)

    assert str(currency) == "USD (курс: 90.0)"
    assert repr(currency) == "Currency(code='USD')"
    assert "Счёт 001" in str(account)
    assert "Account(" in repr(account)
    assert str(CurrencyCalculator()) == "Калькулятор валют"
    assert repr(InterestCalculator()) == "InterestCalculator()"
