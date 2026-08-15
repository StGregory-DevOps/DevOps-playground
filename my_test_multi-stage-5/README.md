# contact-api — Практическое задание №3: Docker Multi-Stage Build

## Описание проекта

REST API для управления контактами (Contact Book) на FastAPI + SQLite.

### Эндпоинты

| Метод  | Путь                 | Описание                  |
|--------|----------------------|---------------------------|
| GET    | /ping                | Проверка состояния        |
| GET    | /contacts            | Список всех контактов     |
| POST   | /contacts            | Создать контакт           |
| GET    | /contacts/{id}       | Получить контакт по ID    |
| PATCH  | /contacts/{id}       | Обновить контакт          |
| DELETE | /contacts/{id}       | Удалить контакт           |

Swagger UI: `http://localhost:7500/docs`

---

## Структура проекта

```
contact-api/
├── app/
│   ├── __init__.py
│   ├── main.py        # FastAPI endpoints
│   ├── database.py    # SQLAlchemy engine + session
│   ├── models.py      # ORM модель Contact
│   └── schemas.py     # Pydantic схемы
├── requirements.txt
├── README.md
├── Dockerfile         # ← создаёшь сам
└── docker-compose.yml # ← создаёшь сам
```

---

## Твоё задание

### Требования к Dockerfile

**Stage 1: `builder`**
- Базовый образ: `python:3.12-slim`
- Рабочая папка: `/workspace`
- venv создать в `/opt/venv`
- Установить зависимости из `requirements.txt`
- Использовать флаг `--no-cache-dir` при установке

**Stage 2: `runtime`**
- Базовый образ: `python:3.12-slim`
- Пользователь: `apiuser`
- Скопировать `/opt/venv` из builder с правами `apiuser`
- Рабочая папка: `/app`
- Скопировать папку `app/` с правами `apiuser`
- Создать папку для базы данных: `/app/contacts_data`
- `DATABASE_URL`: `sqlite:////app/contacts_data/contacts.db`
- Порт: `7500`
- CMD: `uvicorn app.main:app --host 0.0.0.0 --port 7500`

### Требования к docker-compose.yml

- Сервис: `contact-api`
- Имя контейнера: `contact-api-container`
- Порт: `7500:7500`
- Именованный volume: `contacts_data` примонтирован в `/app/contacts_data`
- Передать `DATABASE_URL` через environment

---

## Проверка после запуска

```bash
# Создать контакт
curl -X POST http://localhost:7500/contacts \
  -H "Content-Type: application/json" \
  -d '{"name": "Григорій", "phone": "+380991234567", "email": "greg@example.com"}'

# Список контактов
curl http://localhost:7500/contacts

# Ping
curl http://localhost:7500/ping
```
