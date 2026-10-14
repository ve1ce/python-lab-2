import os
import sqlite3
from pathlib import Path


# Путь к файлу базы данных
DB_PATH = Path(
    os.environ.get(
        "CURRENCY_DB_PATH",
        str(Path(__file__).resolve().parent / "currency_lab.db")
    )
)


def initialize_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)

    try:
        # Таблица валютных операций
        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                source_currency TEXT NOT NULL,
                target_currency TEXT NOT NULL,
                amount REAL NOT NULL,
                exchange_rate REAL NOT NULL,
                commission_percent REAL NOT NULL,
                converted_amount REAL NOT NULL,
                commission REAL NOT NULL,
                final_amount REAL NOT NULL
            )
        """)

        # Таблица расчётов процентов
        connection.execute("""
            CREATE TABLE IF NOT EXISTS interest_calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                currency TEXT NOT NULL,
                balance REAL NOT NULL,
                annual_rate REAL NOT NULL,
                days INTEGER NOT NULL,
                interest_amount REAL NOT NULL
            )
        """)

        connection.commit()

    finally:
        connection.close()


def save_conversion(data):
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("""
            INSERT INTO conversions (
                source_currency,
                target_currency,
                amount,
                exchange_rate,
                commission_percent,
                converted_amount,
                commission,
                final_amount
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["source"],
            data["target"],
            data["amount"],
            data["exchange_rate"],
            data["commission_percent"],
            data["converted_amount"],
            data["commission"],
            data["final_amount"]
        ))

        connection.commit()

    finally:
        connection.close()


def save_interest(data):
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("""
            INSERT INTO interest_calculations (
                currency,
                balance,
                annual_rate,
                days,
                interest_amount
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            data["currency"],
            data["balance"],
            data["annual_rate"],
            data["days"],
            data["result"]
        ))

        connection.commit()

    finally:
        connection.close()