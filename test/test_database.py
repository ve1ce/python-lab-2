
import sqlite3
from contextlib import closing

import pytest
import database

from currency_package.models import Currency, Account, Transaction
from currency_package.calculations import CurrencyCalculator, InterestCalculator


# Создаём отдельную временную базу для каждого теста
@pytest.fixture
def test_db(tmp_path, monkeypatch):
    test_path = tmp_path / "test_currency.db"

    monkeypatch.setattr(database, "DB_PATH", test_path)

    database.initialize_database()

    return test_path


# Тест 1. Проверка создания таблиц
def test_database_creation(test_db):
    assert test_db.exists()

    with closing(sqlite3.connect(test_db)) as connection:
        tables = connection.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table'
        """).fetchall()

    table_names = [table[0] for table in tables]

    assert "conversions" in table_names
    assert "interest_calculations" in table_names


# Тест 2. Проверка сохранения конвертации
def test_save_conversion(test_db):
    usd = Currency("USD")
    eur = Currency("EUR")

    account = Account("001", usd, 500)
    transaction = Transaction(account, eur, 100, 2)

    result = CurrencyCalculator.calculate(transaction)

    data = {
        "source": usd.code,
        "target": eur.code,
        "amount": 100,
        "commission_percent": 2,
        **result
    }

    database.save_conversion(data)

    with closing(sqlite3.connect(test_db)) as connection:
        row = connection.execute("""
            SELECT
                source_currency,
                target_currency,
                amount,
                exchange_rate,
                commission_percent,
                converted_amount,
                commission,
                final_amount
            FROM conversions
        """).fetchone()

    assert row is not None
    assert row[0] == "USD"
    assert row[1] == "EUR"
    assert row[2:] == pytest.approx(
        (100.0, 0.9, 2.0, 90.0, 1.8, 88.2)
    )


# Тест 3. Проверка сохранения процентов
def test_save_interest(test_db):
    usd = Currency("USD")
    account = Account("001", usd, 500)

    interest = InterestCalculator.calculate(account, 5, 30)

    data = {
        "currency": usd.code,
        "balance": 500,
        "annual_rate": 5,
        "days": 30,
        "result": interest
    }

    database.save_interest(data)

    with closing(sqlite3.connect(test_db)) as connection:
        row = connection.execute("""
            SELECT
                currency,
                balance,
                annual_rate,
                days,
                interest_amount
            FROM interest_calculations
        """).fetchone()

    assert row is not None
    assert row[0] == "USD"
    assert row[1:] == pytest.approx(
        (500.0, 5.0, 30, 2.05)
    )


# Тест 4. Проверка сохранности данных
def test_database_persistence(test_db):
    data = {
        "currency": "EUR",
        "balance": 1000,
        "annual_rate": 10,
        "days": 30,
        "result": 8.22
    }

    database.save_interest(data)

    # Повторно инициализируем существующую базу
    database.initialize_database()

    with closing(sqlite3.connect(test_db)) as connection:
        count = connection.execute("""
            SELECT COUNT(*) FROM interest_calculations
        """).fetchone()[0]

    # Запись не должна исчезнуть
    assert count == 1
