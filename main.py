import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from currency_package.models import Currency, Account, Transaction
from currency_package.calculations import CurrencyCalculator, InterestCalculator
from currency_package.reports import export_report



def main():
    # Создаём главное окно
    root = tk.Tk()
    root.title("Лабораторная №2 — Курсы валют")
    root.geometry("520x600")
    root.resizable(False, False)

    # Переменные интерфейса
    source_var = tk.StringVar(value="USD")
    target_var = tk.StringVar(value="RUB")
    amount_var = tk.StringVar(value="100")
    commission_var = tk.StringVar(value="2")

    balance_var = tk.StringVar(value="500")
    rate_var = tk.StringVar(value="5")
    days_var = tk.StringVar(value="30")

    conversion_result = tk.StringVar(value="Результат появится здесь")
    interest_result = tk.StringVar(value="Результат появится здесь")

    # Последние результаты вычислений
    last_results = {
        "conversion": None,
        "interest": None
    }

    # Функция конвертации валют
    def convert_currency():
        try:
            source = Currency(source_var.get())
            target = Currency(target_var.get())

            amount = float(amount_var.get())
            commission = float(commission_var.get())

            account = Account("001", source)

            transaction = Transaction(
                account,
                target,
                amount,
                commission
            )

            result = CurrencyCalculator.calculate(transaction)

            last_results["conversion"] = {
                "source": source.code,
                "target": target.code,
                "amount": amount,
                "commission_percent": commission,
                **result
            }

            conversion_result.set(
                f"Сумма: {result['converted_amount']:.2f} {target.code}\n"
                f"Комиссия: {result['commission']:.2f} {target.code}\n"
                f"Итого: {result['final_amount']:.2f} {target.code}"
            )

        except ValueError as error:
            messagebox.showerror("Ошибка", str(error))

    # Функция расчёта процентов
    def calculate_interest():
        try:
            currency = Currency(source_var.get())

            balance = float(balance_var.get())
            annual_rate = float(rate_var.get())
            days = int(days_var.get())

            account = Account("001", currency, balance)

            interest = InterestCalculator.calculate(
                account,
                annual_rate,
                days
            )

            last_results["interest"] = {
                "currency": currency.code,
                "balance": balance,
                "annual_rate": annual_rate,
                "days": days,
                "result": interest
            }

            interest_result.set(
                f"Начисленные проценты: {interest:.2f} {currency.code}"
            )

        except ValueError as error:
            messagebox.showerror("Ошибка", str(error))

    def save_report():
        # Проверяем наличие результатов
        if all(value is None for value in last_results.values()):
            messagebox.showwarning(
                "Нет данных",
                "Сначала выполните хотя бы один расчёт."
            )
            return

        # Выбираем место сохранения
        file_path = filedialog.asksaveasfilename(
            title="Сохранить отчёт",
            defaultextension=".docx",
            filetypes=[("Документ Word", "*.docx")],
            initialfile="currency_report.docx"
        )

        if not file_path:
            return

        try:
            export_report(
                file_path,
                conversion=last_results["conversion"],
                interest=last_results["interest"]
            )

            messagebox.showinfo(
                "Успешно",
                "Отчёт успешно сохранён!"
            )

        except Exception as error:
            messagebox.showerror(
                "Ошибка сохранения",
                str(error)
            )

    # Заголовок приложения
    ttk.Label(
        root,
        text="Курсы валют",
        font=("Arial", 18, "bold")
    ).pack(pady=12)

    # Блок конвертации валют
    conversion_frame = ttk.LabelFrame(
        root,
        text="Конвертация валют",
        padding=12
    )
    conversion_frame.pack(fill="x", padx=20, pady=5)

    ttk.Label(conversion_frame, text="Исходная валюта:").grid(
        row=0, column=0, sticky="w", pady=3
    )

    ttk.Combobox(
        conversion_frame,
        textvariable=source_var,
        values=["RUB", "USD", "EUR"],
        state="readonly",
        width=17
    ).grid(row=0, column=1, pady=3)

    ttk.Label(conversion_frame, text="Целевая валюта:").grid(
        row=1, column=0, sticky="w", pady=3
    )

    ttk.Combobox(
        conversion_frame,
        textvariable=target_var,
        values=["RUB", "USD", "EUR"],
        state="readonly",
        width=17
    ).grid(row=1, column=1, pady=3)

    ttk.Label(conversion_frame, text="Сумма:").grid(
        row=2, column=0, sticky="w", pady=3
    )

    ttk.Entry(
        conversion_frame, textvariable=amount_var
    ).grid(row=2, column=1, pady=3)

    ttk.Label(conversion_frame, text="Комиссия (%):").grid(
        row=3, column=0, sticky="w", pady=3
    )

    ttk.Entry(
        conversion_frame, textvariable=commission_var
    ).grid(row=3, column=1, pady=3)

    ttk.Button(
        conversion_frame,
        text="Конвертировать",
        command=convert_currency
    ).grid(row=4, column=0, columnspan=2, pady=8)

    ttk.Label(
        conversion_frame,
        textvariable=conversion_result,
        justify="left"
    ).grid(row=5, column=0, columnspan=2, pady=5)

    # Блок расчёта процентов
    interest_frame = ttk.LabelFrame(
        root,
        text="Проценты по счёту",
        padding=12
    )
    interest_frame.pack(fill="x", padx=20, pady=5)

    ttk.Label(interest_frame, text="Баланс счёта:").grid(
        row=0, column=0, sticky="w", pady=3
    )

    ttk.Entry(
        interest_frame, textvariable=balance_var
    ).grid(row=0, column=1, pady=3)

    ttk.Label(interest_frame, text="Годовая ставка (%):").grid(
        row=1, column=0, sticky="w", pady=3
    )

    ttk.Entry(
        interest_frame, textvariable=rate_var
    ).grid(row=1, column=1, pady=3)

    ttk.Label(interest_frame, text="Количество дней:").grid(
        row=2, column=0, sticky="w", pady=3
    )

    ttk.Entry(
        interest_frame, textvariable=days_var
    ).grid(row=2, column=1, pady=3)

    ttk.Button(
        interest_frame,
        text="Рассчитать проценты",
        command=calculate_interest
    ).grid(row=3, column=0, columnspan=2, pady=8)

    ttk.Label(
        interest_frame,
        textvariable=interest_result
    ).grid(row=4, column=0, columnspan=2, pady=5)

    ttk.Button(
        root,
        text="Сохранить отчёт в Word",
        command=save_report
    ).pack(pady=12)

    root.mainloop()


if __name__ == "__main__":
    main()
