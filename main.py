
import math
import sqlite3
from pathlib import Path

from currency_package.models import Currency, Account, Transaction
from currency_package.calculations import CurrencyCalculator, InterestCalculator
from currency_package.reports import export_report

from database import (
    DB_PATH,
    initialize_database,
    save_conversion,
    save_interest
)


# Ввод числового значения
def read_number(message):
    value = float(input(message).strip().replace(",", "."))

    if not math.isfinite(value):
        raise ValueError("Введите корректное конечное число")

    return value


# Конвертация валют
def convert_currency(last_results):
    print("\n=== Конвертация валют ===")
    print("Доступные валюты:", ", ".join(Currency.RATES.keys()))

    source = Currency(input("Исходная валюта: ").strip())
    target = Currency(input("Целевая валюта: ").strip())

    amount = read_number("Сумма: ")
    commission = read_number("Комиссия (%): ")

    # Создаём объекты
    account = Account("001", source)

    transaction = Transaction(
        account,
        target,
        amount,
        commission
    )

    # Выполняем расчёт
    result = CurrencyCalculator.calculate(transaction)

    # Подготавливаем данные для сохранения
    data = {
        "source": source.code,
        "target": target.code,
        "amount": amount,
        "commission_percent": commission,
        **result
    }

    # Сохраняем в SQLite
    save_conversion(data)

    # Запоминаем результат для Word-отчёта
    last_results["conversion"] = data

    print("\n=== Результат конвертации ===")
    print(
        f"Курс: 1 {source.code} = "
        f"{result['exchange_rate']:.4f} {target.code}"
    )
    print(f"Сумма: {result['converted_amount']:.2f} {target.code}")
    print(f"Комиссия: {result['commission']:.2f} {target.code}")
    print(f"Итого: {result['final_amount']:.2f} {target.code}")
    print("Результат сохранён в SQLite!")


# Расчёт процентов
def calculate_interest(last_results):
    print("\n=== Расчёт процентов ===")
    print("Доступные валюты:", ", ".join(Currency.RATES.keys()))

    currency = Currency(input("Валюта счёта: ").strip())
    balance = read_number("Баланс счёта: ")
    annual_rate = read_number("Годовая ставка (%): ")
    days = int(input("Количество дней: ").strip())

    account = Account("001", currency, balance)

    interest = InterestCalculator.calculate(
        account,
        annual_rate,
        days
    )

    data = {
        "currency": currency.code,
        "balance": balance,
        "annual_rate": annual_rate,
        "days": days,
        "result": interest
    }

    # Сохраняем в SQLite
    save_interest(data)

    # Запоминаем результат для Word-отчёта
    last_results["interest"] = data

    print("\n=== Результат расчёта ===")
    print(f"Начисленные проценты: {interest:.2f} {currency.code}")
    print("Результат сохранён в SQLite!")


# Экспорт в Word
def save_report(last_results):
    if all(value is None for value in last_results.values()):
        print("Сначала выполните хотя бы один расчёт!")
        return

    filename = input(
        "Имя отчёта [currency_report.docx]: "
    ).strip() or "currency_report.docx"

    # Используем только имя файла
    if Path(filename).name != filename:
        raise ValueError("Укажите имя файла без пути к папке")

    if not filename.lower().endswith(".docx"):
        filename += ".docx"

    file_path = DB_PATH.parent / filename

    export_report(
        str(file_path),
        conversion=last_results["conversion"],
        interest=last_results["interest"]
    )

    print(f"Отчёт успешно сохранён: {file_path}")


# Главное меню приложения
def main():
    initialize_database()

    last_results = {
        "conversion": None,
        "interest": None
    }

    while True:
        print("\n========== КУРСЫ ВАЛЮТ ==========")
        print("1. Конвертация валют")
        print("2. Расчёт процентов по счёту")
        print("3. Сохранить отчёт в Word")
        print("0. Выход")
        print("=================================")

        try:
            choice = input("Выберите действие: ").strip()

            if choice == "1":
                convert_currency(last_results)

            elif choice == "2":
                calculate_interest(last_results)

            elif choice == "3":
                save_report(last_results)

            elif choice == "0":
                print("Завершение программы.")
                break

            else:
                print("Неизвестная команда!")

        except (ValueError, sqlite3.Error, OSError) as error:
            print(f"Ошибка: {error}")

        except (KeyboardInterrupt, EOFError):
            print("\nЗавершение программы.")
            break


if __name__ == "__main__":
    main()
