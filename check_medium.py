
from currency_package.models import Currency, Account, Transaction


# Создаём объекты
usd = Currency("USD")
rub = Currency("RUB")

account = Account("001", usd, 500)

transaction = Transaction(
    account,
    rub,
    100,
    2
)

print("=== Проверка Medium ===")

# Проверяем наследование
print(isinstance(account, Account))
print(isinstance(account, Currency))
print(isinstance(account, object))

# Проверяем управляемые атрибуты
print(f"Баланс до изменения: {account.balance}")

account.balance = 1000

print(f"Баланс после изменения: {account.balance}")

# Попытка задать отрицательный баланс
try:
    account.balance = -100
except ValueError as error:
    print(f"Ошибка: {error}")

# Проверяем ограничения комиссии
try:
    transaction.commission_percent = 150
except ValueError as error:
    print(f"Ошибка: {error}")

# Проверяем строковое представление
print(account)
print(repr(transaction))
