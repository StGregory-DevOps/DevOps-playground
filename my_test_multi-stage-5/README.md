# product-api — Практическое задание №4: Docker Multi-Stage Build

## Описание проекту

REST API для управління товарами (Product Catalog) на FastAPI + SQLite.

### Ендпоінти

| Метод  | Шлях                  | Опис                    |
|--------|-----------------------|-------------------------|
| GET    | /status               | Перевірка стану         |
| GET    | /products             | Список усіх товарів     |
| POST   | /products             | Створити товар          |
| GET    | /products/{id}        | Отримати товар по ID    |
| PATCH  | /products/{id}        | Оновити товар           |
| DELETE | /products/{id}        | Видалити товар          |

Swagger UI: `http://localhost:6800/docs`

---

## Структура проекту

```
product-api/
├── app/
│   ├── __init__.py
│   ├── main.py        # FastAPI endpoints
│   ├── database.py    # SQLAlchemy engine + session
│   ├── models.py      # ORM модель Product
│   └── schemas.py     # Pydantic схеми
├── requirements.txt
├── README.md
├── Dockerfile         # ← створюєш сам
└── docker-compose.yml # ← створюєш сам
```

---

## Твоє завдання

### Вимоги до Dockerfile

**Stage 1: `builder`**
- Базовий образ: `python:3.11-slim`
- Робоча папка: `/deps`
- venv створити в `/opt/venv`
- Встановити залежності з `requirements.txt`
- Використати прапор `--no-cache-dir` при встановленні

**Stage 2: `runtime`**
- Базовий образ: `python:3.11-slim`
- Користувач: `produser`
- Скопіювати `/opt/venv` з builder з правами `produser`
- Активувати venv через ENV PATH
- Робоча папка: `/app`
- Скопіювати папку `app/` з правами `produser`
- Створити папку для бази даних: `/app/db`
- `DATABASE_URL`: `sqlite:////app/db/products.db`
- Порт: `6800`
- CMD: `uvicorn app.main:app --host 0.0.0.0 --port 6800`

### Вимоги до docker-compose.yml

- Сервіс: `product-api`
- Ім'я контейнера: `product-api-container`
- Порт: `6800:6800`
- Іменований volume: `product_db` змонтований в `/app/db`
- Передати `DATABASE_URL` через environment

---

## Перевірка після запуску
**Документація FastAPI в браузері:**
   http://localhost:6800/docs

```bash
# Створити товар
curl -X POST http://localhost:6800/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Ноутбук", "description": "ASUS VivoBook", "price": 25000.00, "in_stock": true}'

# Список товарів
curl http://localhost:6800/products

# Статус
curl http://localhost:6800/status
```

---

## Підказки

- Фреймворк: **FastAPI** — команда запуску через `uvicorn`
- База даних: **SQLite** — файл зберігається в `/app/db/`
- Порт додатку: **6800**
- Папка з кодом: **app/**
