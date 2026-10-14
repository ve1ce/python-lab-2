import os
import sqlite3
from pathlib import Path

from currency_package.models import Currency, Account, Transaction
from currency_package.calculations import CurrencyCalculator


# Путь можно изменить через переменную окружения (например, в Docker).
DB_PATH = Path(os.environ.get(
    "CURRENCY_DB_PATH",
    str(Path(__file__).resolve().parent / "currency_lab.db")
))


def initialize_database():
    """Создаёт таблицы, если база запускается впервые."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS interest_calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                currency TEXT NOT NULL,
                balance REAL NOT NULL,
                annual_rate REAL NOT NULL,
                days INTEGER NOT NULL,
                interest_amount REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                currency TEXT NOT NULL,
                balance REAL NOT NULL DEFAULT 0 CHECK(balance >= 0),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            );

            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                source_account_id INTEGER NOT NULL,
                target_account_id INTEGER NOT NULL,
                source_currency TEXT NOT NULL,
                target_currency TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                exchange_rate REAL NOT NULL,
                commission_percent REAL NOT NULL,
                converted_amount REAL NOT NULL,
                commission REAL NOT NULL,
                received_amount REAL NOT NULL,
                FOREIGN KEY (source_account_id) REFERENCES accounts(id),
                FOREIGN KEY (target_account_id) REFERENCES accounts(id)
            );
        """)
        connection.commit()
    finally:
        connection.close()


def save_interest(data):
    """Сохраняет результат расчёта процентов."""
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute("""
            INSERT INTO interest_calculations
                (currency, balance, annual_rate, days, interest_amount)
            VALUES (?, ?, ?, ?, ?)
        """, (data["currency"], data["balance"], data["annual_rate"],
              data["days"], data["result"]))
        connection.commit()
    finally:
        connection.close()


def create_account(currency_code):
    """Создаёт пустой счёт и возвращает объект Account."""
    currency = Currency(currency_code)
    connection = sqlite3.connect(DB_PATH)
    try:
        cursor = connection.execute(
            "INSERT INTO accounts (currency, balance) VALUES (?, ?)",
            (currency.code, 0.0)
        )
        connection.commit()
        return Account(str(cursor.lastrowid), currency, 0)
    finally:
        connection.close()


def get_accounts():
    """Возвращает все счета в порядке их создания."""
    connection = sqlite3.connect(DB_PATH)
    try:
        rows = connection.execute(
            "SELECT id, currency, balance FROM accounts ORDER BY id"
        ).fetchall()
        return [Account(str(id_), Currency(code), balance)
                for id_, code, balance in rows]
    finally:
        connection.close()


def _get_account(connection, account_id, error_message):
    """Находит счёт и превращает запись SQLite в объект Account."""
    row = connection.execute(
        "SELECT id, currency, balance FROM accounts WHERE id = ?",
        (account_id,)
    ).fetchone()
    if row is None:
        raise ValueError(error_message)
    return Account(str(row[0]), Currency(row[1]), row[2])


def deposit_to_account(account_id, amount):
    """Пополняет счёт и записывает пополнение в историю."""
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")

        account = _get_account(connection, account_id, "Счёт не найден")
        account.deposit(amount)  # Проверка суммы выполняется в Account.

        connection.execute(
            "UPDATE accounts SET balance = ? WHERE id = ?",
            (account.balance, account_id)
        )
        connection.execute(
            "INSERT INTO deposits (account_id, amount) VALUES (?, ?)",
            (account_id, round(float(amount), 2))
        )
        connection.commit()
        return account
    except Exception:
        connection.rollback()  # Ошибка не должна менять баланс.
        raise
    finally:
        connection.close()


def execute_transfer(source_id, target_id, amount, commission_percent):
    """Переводит деньги между счетами одной SQL-транзакцией."""
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")

        source = _get_account(connection, source_id, "Счёт отправителя не найден")
        target = _get_account(connection, target_id, "Счёт получателя не найден")
        if source.number == target.number:
            raise ValueError("Нельзя переводить деньги на тот же счёт")

        # Расчёты делает калькулятор, а проверку баланса — Account.
        transaction = Transaction(source, target.currency, amount, commission_percent)
        result = CurrencyCalculator.calculate_transfer(transaction)
        source.withdraw(transaction.amount)
        target.deposit(result["final_amount"])

        # Оба баланса и история сохраняются вместе.
        for account in (source, target):
            connection.execute(
                "UPDATE accounts SET balance = ? WHERE id = ?",
                (account.balance, account.number)
            )

        cursor = connection.execute("""
            INSERT INTO transfers (
                source_account_id, target_account_id,
                source_currency, target_currency, amount, exchange_rate,
                commission_percent, converted_amount, commission, received_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source.number, target.number,
            source.currency.code, target.currency.code,
            transaction.amount, result["exchange_rate"],
            transaction.commission_percent, result["converted_amount"],
            result["commission"], result["final_amount"]
        ))
        connection.commit()

        return {
            "transfer_id": cursor.lastrowid,
            "source_account_id": source.number,
            "target_account_id": target.number,
            "source_currency": source.currency.code,
            "target_currency": target.currency.code,
            "amount": transaction.amount,
            "commission_percent": transaction.commission_percent,
            "source_balance": source.balance,
            "target_balance": target.balance,
            **result
        }
    except Exception:
        connection.rollback()  # Если перевод не удался, отменяем всё.
        raise
    finally:
        connection.close()


def get_table_data(table_name):
    """Возвращает последние 20 записей таблицы для меню и Excel."""
    allowed_tables = (
        "accounts", "deposits", "transfers", "interest_calculations"
    )
    if table_name not in allowed_tables:
        raise ValueError("Неизвестная таблица базы данных")

    connection = sqlite3.connect(DB_PATH)
    try:
        cursor = connection.execute(
            f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 20"
        )
        columns = [item[0] for item in cursor.description]
        return columns, cursor.fetchall()
    finally:
        connection.close()
