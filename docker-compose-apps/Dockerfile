FROM python:3.11-slim

WORKDIR /app

# Сначала ставим системные зависимости для сборки бинарников (нужно для некоторых библиотек БД)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Копируем сначала зависимости, чтобы кэшировать этот слой (ускоряет деплой)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё остальное приложение
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
