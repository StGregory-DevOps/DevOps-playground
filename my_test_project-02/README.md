# Task Manager API 🐳

Учебный pet-проект: REST API на Flask, обёрнутое в Docker Compose с PostgreSQL,
Redis и Nginx в качестве reverse proxy.

Цель проекта — практика с Docker: multi-stage работа с Dockerfile, healthcheck'и,
изоляция сети, персистентность данных через volumes.

## Стек

- Python 3.12 / Flask — REST API
- PostgreSQL 16 — основное хранилище
- Redis 7 — кэширование GET-запросов
- Nginx — reverse proxy
- Docker Compose — оркестрация сервисов

## Архитектура

Client → Nginx (:80) → Backend (Flask/Gunicorn) → PostgreSQL
                                    ↓
                                  Redis (кэш)
Наружу открыт только Nginx. Backend, БД и кэш находятся во внутренней Docker-сети
и недоступны извне напрямую.

## Быстрый старт

git clone <ссылка на репозиторий>
cd task-manager-api
cp .env.example .env      # заполнить своими значениями
docker compose up -d --build
Проверка:

curl http://localhost:<PORT>/health
# {"status": "ok"}
## API

| Метод | Путь | Описание |
|---|---|---|
| GET | /health | проверка живости сервиса |
| GET | /tasks | список задач (с кэшем на CACHE_TTL сек) |
| POST | /tasks | создать задачу {"title": "string"} |
| PATCH | /tasks/<id>/done | отметить задачу выполненной |

Пример:

curl -X POST http://localhost:<PORT>/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Разобраться с healthcheck в compose"}'
## Структура проекта

.
├── app/
│   ├── app.py
│   └── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
## Что отработано в проекте

- multi-service docker-compose.yml (4 сервиса)
- healthcheck + depends_on: condition: service_healthy, а не просто порядок старта
- изоляция сети — наружу торчит только nginx
- персистентность данных Postgres через named volume
- конфигурация через .env / переменные окружения, без хардкода секретов в коде

## Лицензия

Pet-проект для практики, использовать свободно.
