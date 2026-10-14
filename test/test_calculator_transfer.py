import pytest

from currency_package.models import Currency, Account, Transaction
from currency_package.calculations import CurrencyCalculator


def test_calculate_transfer_success():
    account = Account("001", Currency("USD"), 500)

    transaction = Transaction(
        account,
        Currency("EUR"),
        100,
        2
    )

    result = CurrencyCalculator.calculate_transfer(transaction)

    assert result["exchange_rate"] == 0.9
    assert result["converted_amount"] == 90
    assert result["commission"] == 1.8
    assert result["final_amount"] == 88.2


def test_calculate_transfer_full_commission():
    account = Account("001", Currency("USD"), 500)

    transaction = Transaction(
        account,
        Currency("EUR"),
        100,
        100
    )

    with pytest.raises(ValueError, match="сумма зачисления"):
        CurrencyCalculator.calculate_transfer(transaction)


def test_calculate_transfer_too_small_result():
    account = Account("001", Currency("JPY"), 100)

    transaction = Transaction(
        account,
        Currency("GBP"),
        0.01,
        0
    )

    with pytest.raises(ValueError, match="сумма зачисления"):
        CurrencyCalculator.calculate_transfer(transaction)
