
# Используем готовый образ Python
FROM python:3.12-slim

# Рабочая папка внутри контейнера
WORKDIR /app

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV CURRENCY_DB_PATH=/app/data/currency_lab.db

# Копируем список библиотек
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения
COPY . .

# Создаём папку для базы данных и отчётов
RUN mkdir -p /app/data

# Запускаем нашу программу
CMD ["python", "main.py"]
