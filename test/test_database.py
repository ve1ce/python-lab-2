import sqlite3
from contextlib import closing

import pytest
import database


# Каждый тест работает со своей временной базой, не затрагивая данные программы.
@pytest.fixture
def test_db(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", path)
    database.initialize_database()
    return path


# Все таблицы создаются, а повторный запуск не удаляет записи.
def test_database_creation(test_db):
    with closing(sqlite3.connect(test_db)) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()

    tables = {row[0] for row in rows}
    assert {"accounts", "deposits", "transfers", "interest_calculations"} <= tables

    database.create_account("USD")
    database.initialize_database()
    assert len(database.get_accounts()) == 1


# Создание счетов и загрузка их из базы.
def test_create_accounts(test_db):
    first = database.create_account("USD")
    second = database.create_account("EUR")
    accounts = database.get_accounts()

    assert first.number == "1"
    assert second.number == "2"
    assert [account.currency.code for account in accounts] == ["USD", "EUR"]
    assert all(account.balance == 0 for account in accounts)


# Пополнение меняет баланс и добавляет запись в историю.
def test_deposit(test_db):
    account = database.create_account("USD")
    updated = database.deposit_to_account(account.number, 500)

    assert updated.balance == 500
    assert database.get_accounts()[0].balance == 500

    columns, rows = database.get_table_data("deposits")
    deposit = dict(zip(columns, rows[0]))
    assert deposit["account_id"] == 1
    assert deposit["amount"] == 500


# Неправильное пополнение не меняет базу.
def test_invalid_deposit(test_db):
    account = database.create_account("EUR")

    with pytest.raises(ValueError):
        database.deposit_to_account(account.number, -100)

    assert database.get_accounts()[0].balance == 0
    assert database.get_table_data("deposits")[1] == []


# Результат расчёта процентов сохраняется в SQLite.
def test_save_interest(test_db):
    database.save_interest({
        "currency": "USD", "balance": 500,
        "annual_rate": 5, "days": 30, "result": 2.05
    })

    columns, rows = database.get_table_data("interest_calculations")
    saved = dict(zip(columns, rows[0]))
    assert saved["currency"] == "USD"
    assert saved["interest_amount"] == pytest.approx(2.05)


# Успешный перевод изменяет оба баланса и сохраняется в истории.
def test_successful_transfer(test_db):
    usd = database.create_account("USD")
    eur = database.create_account("EUR")
    database.deposit_to_account(usd.number, 500)
    database.deposit_to_account(eur.number, 200)

    result = database.execute_transfer(usd.number, eur.number, 100, 2)

    assert result["final_amount"] == pytest.approx(88.2)
    assert [a.balance for a in database.get_accounts()] == [400, 288.2]

    columns, rows = database.get_table_data("transfers")
    transfer = dict(zip(columns, rows[0]))
    assert len(rows) == 1
    assert transfer["amount"] == 100
    assert transfer["received_amount"] == pytest.approx(88.2)


# При нехватке денег перевод не выполняется.
def test_insufficient_funds(test_db):
    usd = database.create_account("USD")
    eur = database.create_account("EUR")
    database.deposit_to_account(usd.number, 50)

    with pytest.raises(ValueError, match="Недостаточно средств"):
        database.execute_transfer(usd.number, eur.number, 100, 2)

    assert [a.balance for a in database.get_accounts()] == [50, 0]
    assert database.get_table_data("transfers")[1] == []


# Перевод самому себе запрещён.
def test_transfer_to_same_account(test_db):
    account = database.create_account("USD")
    database.deposit_to_account(account.number, 500)

    with pytest.raises(ValueError, match="тот же счёт"):
        database.execute_transfer(account.number, account.number, 100, 2)

    assert database.get_accounts()[0].balance == 500


# Комиссия 100% не должна приводить к зачислению нулевой суммы.
def test_full_commission(test_db):
    usd = database.create_account("USD")
    eur = database.create_account("EUR")
    database.deposit_to_account(usd.number, 500)

    with pytest.raises(ValueError):
        database.execute_transfer(usd.number, eur.number, 100, 100)

    assert [a.balance for a in database.get_accounts()] == [500, 0]
    assert database.get_table_data("transfers")[1] == []


# При ошибке записи перевода оба баланса откатываются.
def test_transfer_rollback(test_db):
    usd = database.create_account("USD")
    eur = database.create_account("EUR")
    database.deposit_to_account(usd.number, 500)

    # Триггер специально вызывает ошибку при сохранении истории.
    with closing(sqlite3.connect(test_db)) as connection:
        connection.execute("""
            CREATE TRIGGER block_transfer BEFORE INSERT ON transfers
            BEGIN
                SELECT RAISE(ABORT, 'Ошибка сохранения');
            END
        """)
        connection.commit()

    with pytest.raises(sqlite3.IntegrityError):
        database.execute_transfer(usd.number, eur.number, 100, 2)

    assert [a.balance for a in database.get_accounts()] == [500, 0]
    assert database.get_table_data("transfers")[1] == []


# Перевод использует сумму, округлённую до копеек.
def test_transfer_rounding(test_db):
    usd = database.create_account("USD")
    eur = database.create_account("EUR")
    database.deposit_to_account(usd.number, 500)

    result = database.execute_transfer(usd.number, eur.number, 100.567, 2)
    assert result["amount"] == 100.57
    assert result["source_balance"] == 399.43


# Просмотр базы возвращает максимум 20 записей и не принимает чужие таблицы.
def test_get_table_data(test_db):
    for _ in range(25):
        database.create_account("USD")

    columns, rows = database.get_table_data("accounts")
    assert "currency" in columns
    assert len(rows) == 20
    assert rows[0][0] == 25   # Самая новая запись
    assert rows[-1][0] == 6   # Самая старая из показанных

    with pytest.raises(ValueError, match="Неизвестная таблица"):
        database.get_table_data("unknown_table")
