 # Dockerfile for API

FROM python:3.12-slim AS builder

WORKDIR /app

# Устанавливаем тяжелые компиляторы (gcc) и заголовочные файлы (libpq-dev),необходимые ТОЛЬКО на время сборки  для
# компиляции С-расширений Python (psycopg2).
# В конце очищаем кэш apt-get (list/*), чтобы не раздувать кэш слоев.
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev python3-dev && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv/ 
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

# Устанавливаем ТОЛЬКО легкую рантайм-библиотеку(libpq5), необходимую для выполнения запросов к PostgreSQL в райнтайме.
# Тяжелый компилятор (gcc) сюда НЕ ставится ради безопасности и минимального размера образа.
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser
COPY --from=builder --chown=appuser:appuser /opt/venv/ /opt/venv/
ENV PATH="/opt/venv/bin:$PATH"
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 