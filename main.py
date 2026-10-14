import math
import sqlite3
from pathlib import Path

from currency_package.models import Currency, Account, Transaction
from currency_package.calculations import CurrencyCalculator, InterestCalculator
from currency_package.reports import export_report, export_excel
from database import (
    DB_PATH, initialize_database, save_interest, create_account,
    get_accounts, deposit_to_account, execute_transfer, get_table_data
)


# Таблицы, доступные для просмотра и экспорта в Excel.
TABLES = {
    "1": ("accounts", "Банковские счета"),
    "2": ("deposits", "История пополнений"),
    "3": ("transfers", "История переводов"),
    "4": ("interest_calculations", "История расчётов процентов")
}


class ReturnToMenu(Exception):
    """Позволяет выйти из любой операции по команде 0."""


def ask_input(message):
    value = input(message).strip()
    if value == "0":
        raise ReturnToMenu
    return value


def read_number(message):
    # Принимаем как точку, так и запятую в десятичном числе.
    number = float(ask_input(message).replace(",", "."))
    if not math.isfinite(number):
        raise ValueError("Введите корректное число")
    return number


def report_path(default_name):
    # Оба отчёта сохраняются рядом с файлом SQLite, в папке data.
    filename = ask_input(f"Имя файла [{default_name}]: ") or default_name
    if Path(filename).name != filename:
        raise ValueError("Укажите имя файла без пути к папке")

    extension = Path(default_name).suffix
    if not filename.lower().endswith(extension):
        filename += extension
    return DB_PATH.parent / filename


def create_account_menu():
    """Создание нового счёта с нулевым балансом."""
    print("\n=== СОЗДАНИЕ СЧЁТА ===")
    print("Доступные валюты:", ", ".join(Currency.RATES))
    print("0. Вернуться в главное меню")

    account = create_account(ask_input("Валюта счёта: "))
    print(f"\nСчёт успешно создан: {account}")


def show_accounts_menu(accounts=None):
    """Вывод счетов; список можно передать, чтобы не читать БД повторно."""
    if accounts is None:
        accounts = get_accounts()

    print("\n=== СПИСОК СЧЕТОВ ===")
    if not accounts:
        print("Счета ещё не созданы.")
        return

    print(f"{'Номер':<10} {'Валюта':<10} {'Баланс':>15}")
    print("-" * 37)
    for account in accounts:
        print(f"{account.number:<10} {account.currency.code:<10} {account.balance:>15.2f}")


def deposit_account_menu():
    """Пополнение выбранного счёта."""
    accounts = get_accounts()
    if not accounts:
        print("Сначала необходимо создать счёт.")
        return

    show_accounts_menu(accounts)
    print("0. Вернуться в главное меню")
    account_id = ask_input("Номер счёта: ")
    amount = read_number("Сумма пополнения: ")

    account = deposit_to_account(account_id, amount)
    print(f"\nСчёт пополнен. Текущий баланс: {account.balance:.2f} {account.currency.code}")


def transfer_currency():
    """Показывает расчёт и выполняет перевод только после подтверждения Y."""
    accounts = get_accounts()
    if len(accounts) < 2:
        print("Для перевода необходимо создать минимум два счёта.")
        return

    show_accounts_menu(accounts)
    print("0. Вернуться в главное меню")
    accounts_by_number = {account.number: account for account in accounts}

    source_number = ask_input("\nНомер счёта отправителя: ")
    target_number = ask_input("Номер счёта получателя: ")

    if source_number not in accounts_by_number:
        raise ValueError("Счёт отправителя не найден")
    if target_number not in accounts_by_number:
        raise ValueError("Счёт получателя не найден")
    if source_number == target_number:
        raise ValueError("Нельзя переводить деньги на тот же счёт")

    source = accounts_by_number[source_number]
    target = accounts_by_number[target_number]
    amount = read_number("Сумма перевода: ")
    commission_text = ask_input("Комиссия (%), Enter — без комиссии: ")
    commission = float(commission_text.replace(",", ".")) if commission_text else 0.0

    # Модель проверяет сумму и комиссию, а калькулятор — итог конвертации.
    transaction = Transaction(source, target.currency, amount, commission)
    if not source.can_withdraw(transaction.amount):
        raise ValueError("Недостаточно средств на счёте отправителя")
    result = CurrencyCalculator.calculate_transfer(transaction)

    print("\n=== ПОДТВЕРЖДЕНИЕ ПЕРЕВОДА ===")
    print(f"Отправитель: счёт №{source.number} ({source.currency.code})")
    print(f"Получатель: счёт №{target.number} ({target.currency.code})")
    print(f"Списание: {transaction.amount:.2f} {source.currency.code}")
    print(f"Курс: 1 {source.currency.code} = {result['exchange_rate']:.4f} {target.currency.code}")
    print(f"После обмена: {result['converted_amount']:.2f} {target.currency.code}")
    print(f"Комиссия ({transaction.commission_percent}%): {result['commission']:.2f} {target.currency.code}")
    print(f"К зачислению: {result['final_amount']:.2f} {target.currency.code}")

    # До подтверждения никакие изменения в SQLite не вносятся.
    print("\nПодтвердить перевод? (Y/N), 0 — главное меню")
    while True:
        choice = ask_input("Ваш выбор: ").lower()
        if choice == "n":
            print("Перевод отменён. Балансы не изменены.")
            return
        if choice == "y":
            break
        print("Введите Y или N.")

    operation = execute_transfer(
        source_number, target_number,
        transaction.amount, transaction.commission_percent
    )
    print("\n=== ПЕРЕВОД ВЫПОЛНЕН ===")
    print(f"Номер операции: {operation['transfer_id']}")
    print(f"Списано: {operation['amount']:.2f} {source.currency.code}")
    print(f"Зачислено: {operation['final_amount']:.2f} {target.currency.code}")
    print(f"Остаток счёта №{source.number}: {operation['source_balance']:.2f} {source.currency.code}")
    print(f"Баланс счёта №{target.number}: {operation['target_balance']:.2f} {target.currency.code}")
    print("Операция сохранена в SQLite!")


def calculate_interest():
    """Справочный расчёт процентов без изменения реального баланса."""
    print("\n=== РАСЧЁТ ПРОЦЕНТОВ ===")
    print("Доступные валюты:", ", ".join(Currency.RATES))
    print("0. Вернуться в главное меню")

    currency = Currency(ask_input("Валюта счёта: "))
    balance = read_number("Баланс счёта: ")
    annual_rate = read_number("Годовая ставка (%): ")
    days = int(ask_input("Количество дней: "))

    account = Account("001", currency, balance)
    interest = InterestCalculator.calculate(account, annual_rate, days)
    save_interest({
        "currency": currency.code, "balance": account.balance,
        "annual_rate": annual_rate, "days": days, "result": interest
    })
    print(f"\nРассчитанные проценты: {interest:.2f} {currency.code}")
    print("Результат сохранён в SQLite!")


def save_report():
    """Word: последний перевод и последний расчёт процентов из SQLite."""
    transfer_columns, transfer_rows = get_table_data("transfers")
    interest_columns, interest_rows = get_table_data("interest_calculations")
    if not transfer_rows and not interest_rows:
        print("В базе пока нет переводов или расчётов процентов.")
        return

    conversion = None
    interest = None
    if transfer_rows:
        transfer = dict(zip(transfer_columns, transfer_rows[0]))
        # Имена полей Word-шаблона отличаются от названий в SQLite.
        conversion = {
            **transfer,
            "transfer_id": transfer["id"],
            "source": transfer["source_currency"],
            "target": transfer["target_currency"],
            "final_amount": transfer["received_amount"]
        }
    if interest_rows:
        interest = dict(zip(interest_columns, interest_rows[0]))
        interest["result"] = interest["interest_amount"]

    print("\n=== ЭКСПОРТ В WORD ===")
    print("0. Вернуться в главное меню")
    file_path = report_path("currency_report.docx")
    export_report(str(file_path), conversion=conversion, interest=interest)
    print(f"Word-отчёт успешно сохранён: {file_path}")


def view_database_menu():
    """Просмотр последних 20 записей выбранной таблицы."""
    print("\n=== ПРОСМОТР БАЗЫ ДАННЫХ ===")
    for number, (_, title) in TABLES.items():
        print(f"{number}. {title}")
    print("0. Вернуться в главное меню")

    choice = ask_input("Выберите таблицу: ")
    if choice not in TABLES:
        print("Неизвестная команда!")
        return

    table_name, title = TABLES[choice]
    columns, rows = get_table_data(table_name)
    print(f"\n=== {title.upper()} ===")
    if not rows:
        print("В таблице пока нет записей.")
        return

    print(f"Показано записей: {len(rows)} (не более 20)")
    for row in rows:
        print("\n" + "-" * 40)
        for column, value in zip(columns, row):
            print(f"{column}: {value}")


def save_excel_report():
    """Excel: последние 20 записей из каждой таблицы SQLite."""
    print("\n=== ЭКСПОРТ В EXCEL ===")
    print("В Excel попадут последние 20 записей каждой таблицы.")
    print("0. Вернуться в главное меню")

    file_path = report_path("currency_report.xlsx")
    table_data = {name: get_table_data(name) for name, _ in TABLES.values()}
    export_excel(str(file_path), table_data)
    print(f"Excel-отчёт успешно сохранён: {file_path}")


def main():
    """Главное меню приложения."""
    initialize_database()

    while True:
        print("""
========== КУРСЫ ВАЛЮТ ==========
1. Создать счёт
2. Пополнить счёт
3. Просмотреть счета
4. Перевести средства между счетами
5. Рассчитать проценты
6. Просмотреть базу данных
7. Сохранить отчёт в Word
8. Экспортировать в Excel
0. Выход
=================================""")
        try:
            choice = input("Выберите действие: ").strip()
            if choice == "1":
                create_account_menu()
            elif choice == "2":
                deposit_account_menu()
            elif choice == "3":
                show_accounts_menu()
            elif choice == "4":
                transfer_currency()
            elif choice == "5":
                calculate_interest()
            elif choice == "6":
                view_database_menu()
            elif choice == "7":
                save_report()
            elif choice == "8":
                save_excel_report()
            elif choice == "0":
                print("Завершение программы.")
                break
            else:
                print("Неизвестная команда!")

        except ReturnToMenu:
            print("\nВозврат в главное меню.")
        except (ValueError, sqlite3.Error, OSError) as error:
            print(f"\nОшибка: {error}")
        except (KeyboardInterrupt, EOFError):
            print("\nЗавершение программы.")
            break


if __name__ == "__main__":
    main()
