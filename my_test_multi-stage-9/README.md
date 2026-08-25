# Task Tracker — Docker Multi-Stage Build Project

Учебный проект Junior+. Демонстрирует:
- Multi-stage build (builder → runtime, ≤ 2 стейджа на сервис)
- Non-root user в контейнере
- depends_on с healthcheck condition
- Redis как кэш + очередь
- Воркер, читающий очередь через BLPOP

## Стек

| Сервис   | Образ / язык        | Роль                         |
|----------|---------------------|------------------------------|
| postgres | postgres:16-alpine  | Основная БД                  |
| redis    | redis:7-alpine      | Кэш ответов + очередь задач  |
| api      | python:3.12-slim    | FastAPI REST API             |
| worker   | python:3.12-slim    | Фоновый обработчик очереди   |
| nginx    | nginx:1.27-alpine   | Реверс-прокси, порт 80       |

## Запуск

```bash
# Сборка и запуск всех сервисов
docker compose up --build -d

# Логи всех сервисов
docker compose logs -f

# Логи конкретного сервиса
docker compose logs -f worker

# Статус контейнеров
docker compose ps
```

## API — примеры curl

```bash
# Создать задачу (Nginx → API)
curl -X POST http://localhost/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Deploy to staging", "priority": "high"}'

# Получить все задачи
curl http://localhost/tasks/

# Получить одну задачу
curl http://localhost/tasks/1

# Обновить задачу
curl -X PATCH http://localhost/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated description"}'

# Удалить задачу
curl -X DELETE http://localhost/tasks/1

# Health check
curl http://localhost/health
```

## Swagger UI

Открыть в браузере: http://localhost/docs

## Остановка

```bash
# Остановить без удаления volumes
docker compose down

# Остановить и удалить volumes (БД будет пустой после следующего запуска)
docker compose down -v
```

## Как работает воркер

1. Ты создаёшь задачу → API кладёт job в Redis список `task_queue`
2. Worker делает `BLPOP task_queue` — блокируется, ждёт job
3. Получает job → PATCH `/tasks/{id}/status` → `in_progress`
4. Имитирует работу (sleep 2s)
5. PATCH `/tasks/{id}/status` → `done`

## Commit message для этого проекта

```
feat: add task-tracker multi-stage Docker project with FastAPI, PostgreSQL, Redis, Nginx
```
