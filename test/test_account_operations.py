import pytest

from currency_package.models import Currency, Account


def test_account_deposit():
    account = Account("001", Currency("USD"))

    account.deposit(500)

    assert account.balance == 500


def test_account_withdraw():
    account = Account("001", Currency("USD"), 500)

    account.withdraw(150)

    assert account.balance == 350


def test_insufficient_funds():
    account = Account("001", Currency("USD"), 100)

    with pytest.raises(ValueError, match="Недостаточно средств"):
        account.withdraw(200)

    # После неудачной операции баланс не изменился
    assert account.balance == 100


def test_invalid_account_operations():
    account = Account("001", Currency("EUR"), 100)

    with pytest.raises(ValueError):
        account.deposit(-50)

    with pytest.raises(ValueError):
        account.withdraw(0)

    assert account.balance == 100

def test_can_withdraw_when_enough_money():
    account = Account("001", Currency("USD"), 500)

    assert account.can_withdraw(100) is True

    # Проверка не должна списывать деньги
    assert account.balance == 500


def test_can_withdraw_when_not_enough_money():
    account = Account("001", Currency("USD"), 500)

    assert account.can_withdraw(700) is False

    # Баланс остался прежним
    assert account.balance == 500


def test_can_withdraw_invalid_amount():
    account = Account("001", Currency("EUR"), 500)

    with pytest.raises(ValueError):
        account.can_withdraw(-100)

    with pytest.raises(ValueError):
        account.can_withdraw(0)

    assert account.balance == 500
