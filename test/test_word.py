from docx import Document

import database
import main
from currency_package.reports import export_report


def read_word_text(path):
    """Собирает весь текст из созданного Word-документа."""
    return "\n".join(p.text for p in Document(path).paragraphs)


def test_word_transfer(tmp_path):
    # Проверяем отчёт с одним переводом.
    transfer = {
        "transfer_id": 1,
        "source_account_id": "1",
        "target_account_id": "2",
        "source": "USD",
        "target": "EUR",
        "amount": 100,
        "exchange_rate": 0.9,
        "commission_percent": 2,
        "converted_amount": 90,
        "commission": 1.8,
        "final_amount": 88.2,
        "source_balance": 400,
        "target_balance": 288.2
    }
    path = tmp_path / "transfer.docx"
    export_report(path, conversion=transfer)
    text = read_word_text(path)

    assert "Перевод между счетами" in text
    assert "Счёт отправителя: №1 (USD)" in text
    assert "Счёт получателя: №2 (EUR)" in text
    assert "Комиссия (2%): 1.80 EUR" in text
    assert "Итого к зачислению: 88.20 EUR" in text
    assert "Остаток счёта отправителя: 400.00 USD" in text
    assert "Расчёт процентов по счёту" not in text


def test_word_interest(tmp_path):
    # Проверяем отчёт только с расчётом процентов.
    interest = {
        "currency": "USD",
        "balance": 500,
        "annual_rate": 5,
        "days": 30,
        "result": 2.05
    }
    path = tmp_path / "interest.docx"
    export_report(path, interest=interest)
    text = read_word_text(path)

    assert "Расчёт процентов по счёту" in text
    assert "Годовая ставка: 5%" in text
    assert "Количество дней: 30" in text
    assert "Рассчитанные проценты: 2.05 USD" in text
    assert "Перевод между счетами" not in text


def test_word_from_database(tmp_path, monkeypatch):
    # Используем отдельную SQLite, чтобы не изменять настоящую базу.
    db_path = tmp_path / "test_word.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    monkeypatch.setattr(main, "DB_PATH", db_path)
    database.initialize_database()

    usd = database.create_account("USD")
    eur = database.create_account("EUR")
    database.deposit_to_account(usd.number, 500)
    database.execute_transfer(usd.number, eur.number, 100, 2)
    database.save_interest({
        "currency": "USD", "balance": 500,
        "annual_rate": 5, "days": 30, "result": 2.05
    })

    # Сохраняем отчёт через меню без новых вычислений.
    monkeypatch.setattr("builtins.input", lambda _: "")
    main.save_report()

    path = tmp_path / "currency_report.docx"
    assert path.exists()
    text = read_word_text(path)

    # Оба раздела должны содержать результаты из SQLite.
    assert "Перевод между счетами" in text
    assert "Счёт отправителя: №1 (USD)" in text
    assert "Итого к зачислению: 88.20 EUR" in text
    assert "Расчёт процентов по счёту" in text
    assert "Рассчитанные проценты: 2.05 USD" in text
