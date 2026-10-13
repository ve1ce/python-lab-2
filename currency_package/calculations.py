
class CurrencyCalculator:

    def __str__(self):
        return "Калькулятор валют"

    def __repr__(self):
        return "CurrencyCalculator()"


    @staticmethod
    def calculate(transaction):
        # Получаем курсы валют относительно рубля
        source_rate = transaction.account.currency.rate
        target_rate = transaction.target_currency.rate

        # Рассчитываем обменный курс между валютами
        exchange_rate = source_rate / target_rate

        # Конвертируем сумму
        converted_amount = round(
            transaction.amount * exchange_rate, 2
        )

        # Рассчитываем комиссию
        commission = round(
            converted_amount * transaction.commission_percent / 100, 2
        )

        # Итоговая сумма после комиссии
        final_amount = round(converted_amount - commission, 2)

        return {
            "exchange_rate": exchange_rate,
            "converted_amount": converted_amount,
            "commission": commission,
            "final_amount": final_amount
        }



class InterestCalculator:

    def __str__(self):
        return "Калькулятор процентов"

    def __repr__(self):
        return "InterestCalculator()"

    @staticmethod
    def calculate(account, annual_rate, days):
        if annual_rate < 0:
            raise ValueError(
                "Процентная ставка не может быть отрицательной"
            )

        if days < 0:
            raise ValueError(
                "Количество дней не может быть отрицательным"
            )

        interest = (
            account.balance * annual_rate / 100 * days / 365
        )

        return round(interest, 2)
