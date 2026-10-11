from currency_package.models import Currency, Account, Transaction


def main():
    usd = Currency("USD")
    rub = Currency("RUB")

    account = Account("001", usd, 500)

    transaction = Transaction(
        account=account,
        target_currency=rub,
        amount=100,
        commission_percent=2
    )

    print("=== Currency Manager ===")
    print(usd)
    print(account)
    print(transaction)


if __name__ == "__main__":
    main()
