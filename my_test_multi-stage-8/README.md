# URL Shortener & Analytics — DevOps Practice Project

**Роль:** Junior DevOps Engineer  
**Задача:** написать Dockerfile для каждого сервиса и файл `docker-compose.yml` для оркестрации всей системы.  
**Исходный код готов.** Твоя работа начинается там, где заканчивается код.

---

## Структура проекта

```
url-shortener/
├── api-service/
│   ├── main.py
│   └── requirements.txt
├── worker-service/
│   ├── main.py
│   └── requirements.txt
├── proxy/
│   ├── nginx.conf
│   └── static/
│       ├── 404.html
│       └── 500.html
├── .env.example
├── .env              ← создать из .env.example (в .gitignore)
├── docker-compose.yml  ← написать самому
├── api-service/Dockerfile   ← написать самому
└── worker-service/Dockerfile ← написать самому
```

---

## Архитектура системы

```
                        ┌──────────┐
       :80 (внешний)    │          │
  ─────────────────────►│  proxy   │ (nginx:alpine)
                        │          │
                        └────┬─────┘
                             │ проксирует на :8000
                        ┌────▼──────────┐
                        │  api-service  │ (FastAPI / uvicorn)
                        │  :8000        │
                        └────┬──────────┘
                   read/write│           │ RPUSH click events
                        ┌────▼───┐   ┌──▼────────────┐
                        │ Redis  │   │ worker-service │
                        │  :6379 │◄──│                │
                        └────────┘   └───────┬────────┘
                                             │ INSERT
                                       ┌─────▼──────┐
                                       │ PostgreSQL  │
                                       │   :5432     │
                                       └────────────┘
```

**Потоки данных:**

1. Клиент → `POST /shorten` → api-service → Redis (`SET url:<code>`)
2. Клиент → `GET /r/<code>` → api-service → Redis (`GET`) → `RPUSH click_events`
3. worker-service → Redis (`BLPOP click_events`) → PostgreSQL (`INSERT`)

---

## Задание 1 — Dockerfile для `api-service`

### Требования

| Параметр | Значение |
|---|---|
| Базовый образ (builder) | `python:3.12-alpine` |
| Базовый образ (runtime) | `python:3.12-alpine` |
| Финальный размер образа | **≤ 30 МБ** |
| Пользователь в контейнере | непривилегированный (`appuser`) |
| Точка входа | `uvicorn main:app --host 0.0.0.0 --port 8000` |
| Рабочая директория | `/app` |

### Обязательная структура Multi-Stage Build

**Stage 1 — builder:**
- Установить `gcc`, `musl-dev` (необходимы для сборки некоторых wheels)
- Создать virtualenv в `/opt/venv`
- Активировать venv и установить все зависимости из `requirements.txt` через `pip install --no-cache-dir`

**Stage 2 — runtime:**
- Начать с чистого `python:3.12-alpine` (без build-инструментов)
- Скопировать `/opt/venv` из builder stage
- Добавить `/opt/venv/bin` в `PATH` через `ENV`
- Создать непривилегированного пользователя: `useradd --no-create-home --shell /bin/false appuser`
- Скопировать исходный код (`main.py`)
- Установить `WORKDIR /app`
- Переключиться на `USER appuser`
- Задать `CMD` для запуска uvicorn

### Проверочные команды после сборки

```bash
# Размер образа — должен быть ≤ 30 МБ
docker image inspect url-shortener-api-service --format='{{.Size}}' | awk '{printf "%.1f MB\n", $1/1024/1024}'

# Убедиться что процесс не запущен от root
docker run --rm --entrypoint whoami url-shortener-api-service
# Ожидаемый вывод: appuser

# Убедиться что build-инструменты не попали в финальный образ
docker run --rm url-shortener-api-service sh -c "which gcc || echo 'gcc not found'"
# Ожидаемый вывод: gcc not found
```

---

## Задание 2 — Dockerfile для `worker-service`

### Требования

| Параметр | Значение |
|---|---|
| Базовый образ (builder) | `python:3.12-alpine` |
| Базовый образ (runtime) | `python:3.12-alpine` |
| Финальный размер образа | **≤ 30 МБ** |
| Пользователь в контейнере | непривилегированный (`appuser`) |
| Точка входа | `python main.py` |
| Рабочая директория | `/app` |

### Особенности

`psycopg2-binary` содержит скомпилированные `.so`-файлы — они должны быть скопированы **вместе с venv** из builder stage. Дополнительных системных библиотек в runtime для `psycopg2-binary` **не требуется**.

Структура Multi-Stage Build — идентична `api-service` (builder → runtime, тот же паттерн с `/opt/venv`).

---

## Задание 3 — `docker-compose.yml`

### Обязательные сервисы

| Сервис | Image / Build | Внутренний порт | Внешний порт |
|---|---|---|---|
| `postgres` | `postgres:15-alpine` | 5432 | не пробрасывать |
| `redis` | `redis:7-alpine` | 6379 | не пробрасывать |
| `api-service` | `build: ./api-service` | 8000 | не пробрасывать напрямую |
| `worker-service` | `build: ./worker-service` | — | — |
| `proxy` | `nginx:alpine` | 80 | **80:80** |

### Требования к сетям

- Создать одну кастомную сеть `shortener-net` типа `bridge`
- Все сервисы — в этой сети
- `proxy` — единственная точка входа извне

### Требования к volumes

- Именованный volume `postgres_data` — монтировать в `/var/lib/postgresql/data`
- Конфиг nginx монтировать как **read-only**: `./proxy/nginx.conf:/etc/nginx/nginx.conf:ro`
- Статические страницы nginx монтировать как **read-only**: `./proxy/static:/usr/share/nginx/html/static:ro`

### Требования к переменным окружения

- Все переменные — через `env_file: .env` (не `environment:` с хардкодом значений)
- Исключение: переменные `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` у сервиса `postgres` — тоже из `env_file`

### Требования к `depends_on` + healthcheck

**postgres** должен иметь healthcheck:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

**redis** должен иметь healthcheck:
```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 3s
  retries: 5
```

**api-service** зависит от `redis` с `condition: service_healthy`

**worker-service** зависит от `redis` И `postgres`, оба с `condition: service_healthy`

**proxy** зависит от `api-service` с `condition: service_started`

### Требования к `restart`

- `postgres`, `redis` — `restart: unless-stopped`
- `api-service`, `worker-service` — `restart: on-failure`
- `proxy` — `restart: unless-stopped`

### Требования к `container_name`

Задать явно для каждого сервиса:
- `shortener-postgres`
- `shortener-redis`
- `shortener-api`
- `shortener-worker`
- `shortener-proxy`

---

## Шаги запуска

```bash
# 1. Создать .env
cp .env.example .env

# 2. Собрать образы
docker compose build

# 3. Запустить стек
docker compose up -d

# 4. Проверить статус всех контейнеров
docker compose ps
```

---

## Критерии проверки работы системы

### 1. Все контейнеры запущены и healthy

```bash
docker compose ps
```
**Ожидаемый результат:** все 5 сервисов в состоянии `running`, postgres и redis — `healthy`.

---

### 2. Health endpoint api-service доступен через proxy

```bash
curl -s http://localhost/health | python3 -m json.tool
```
**Ожидаемый результат:**
```json
{
    "status": "ok",
    "redis": "ok"
}
```

---

### 3. Создание короткой ссылки

```bash
curl -s -X POST http://localhost/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://docs.docker.com/compose/"}' | python3 -m json.tool
```
**Ожидаемый результат:** JSON с полями `short_url`, `short_code`, `original_url`, `ttl_seconds`.

Сохрани `short_code` из ответа для следующих шагов.

---

### 4. Редирект по короткой ссылке

```bash
# Замени <code> на short_code из предыдущего шага
curl -s -o /dev/null -w "%{http_code} -> %{redirect_url}\n" http://localhost/r/<code>
```
**Ожидаемый результат:** `302 -> https://docs.docker.com/compose/`

---

### 5. Событие клика попало в очередь Redis

```bash
docker exec shortener-redis redis-cli LLEN click_events
```
**Ожидаемый результат:** `(integer) 0` — очередь должна быть уже дренирована воркером.  
Если воркер не успел: значение > 0, подождать несколько секунд и повторить.

---

### 6. Воркер записал статистику в PostgreSQL

```bash
docker exec shortener-postgres psql -U shortener -d analytics \
  -c "SELECT short_code, total_clicks, last_clicked FROM click_stats;"
```
**Ожидаемый результат:** строка с твоим `short_code` и `total_clicks = 1`.

```bash
docker exec shortener-postgres psql -U shortener -d analytics \
  -c "SELECT id, short_code, raw_ts FROM click_events LIMIT 5;"
```
**Ожидаемый результат:** запись с событием клика.

---

### 7. Метрики API

```bash
curl -s http://localhost/metrics | python3 -m json.tool
```
**Ожидаемый результат:** JSON с `total_stored_urls`, `click_queue_length`, `redis_total_commands_processed`.

---

### 8. Кастомная страница 404

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/r/nonexistent
```
**Ожидаемый результат:** `404` (nginx отдаёт статический `404.html` через `proxy_intercept_errors`).

---

### 9. Проверка размера образов

```bash
docker images | grep url-shortener
```
**Ожидаемый результат:** оба образа (`api-service`, `worker-service`) — **≤ 30 МБ**.

---

### 10. Проверка что процессы не запущены от root

```bash
docker exec shortener-api whoami
docker exec shortener-worker whoami
```
**Ожидаемый результат:** `appuser` для обоих.

---

## Коммит после завершения

После успешного прохождения всех критериев:

```bash
git add .
git commit -m "feat: add url-shortener multi-service docker practice project"
```

---

## Справочник эндпоинтов

| Метод | URL | Описание |
|---|---|---|
| `GET` | `/health` | Проверка работоспособности api-service |
| `GET` | `/metrics` | Метрики Redis и очереди |
| `POST` | `/shorten` | Создать короткую ссылку |
| `GET` | `/r/{code}` | Редирект по короткому коду |
| `GET` | `/urls/{code}` | Информация о ссылке (без редиректа) |
| `GET` | `/nginx-health` | Health probe самого nginx |
