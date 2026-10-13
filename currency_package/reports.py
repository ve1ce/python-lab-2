from docx import Document


def export_report(file_path, conversion=None, interest=None):
    document = Document()

    document.add_heading("Отчёт по валютным операциям", 0)
    document.add_paragraph(
        "Лабораторная работа №2 — Курсы валют"
    )

    # Результаты конвертации
    if conversion is not None:
        document.add_heading("Конвертация валют", level=1)

        document.add_paragraph(
            f"Исходная сумма: {conversion['amount']:.2f} "
            f"{conversion['source']}"
        )

        document.add_paragraph(
            f"Целевая валюта: {conversion['target']}"
        )

        document.add_paragraph(
            f"Обменный курс: 1 {conversion['source']} = "
            f"{conversion['exchange_rate']:.4f} "
            f"{conversion['target']}"
        )

        document.add_paragraph(
            f"Сумма после конвертации: "
            f"{conversion['converted_amount']:.2f} "
            f"{conversion['target']}"
        )

        document.add_paragraph(
            f"Комиссия ({conversion['commission_percent']}%): "
            f"{conversion['commission']:.2f} "
            f"{conversion['target']}"
        )

        document.add_paragraph(
            f"Итого к получению: "
            f"{conversion['final_amount']:.2f} "
            f"{conversion['target']}"
        )

    # Результаты начисления процентов
    if interest is not None:
        document.add_heading("Проценты по счёту", level=1)

        document.add_paragraph(
            f"Баланс счёта: {interest['balance']:.2f} "
            f"{interest['currency']}"
        )

        document.add_paragraph(
            f"Годовая ставка: {interest['annual_rate']}%"
        )

        document.add_paragraph(
            f"Количество дней: {interest['days']}"
        )

        document.add_paragraph(
            f"Начисленные проценты: "
            f"{interest['result']:.2f} "
            f"{interest['currency']}"
        )

    document.add_paragraph(
        "Расчёты выполнены с использованием "
        "фиксированных демонстрационных курсов валют."
    )

    document.save(file_path)
