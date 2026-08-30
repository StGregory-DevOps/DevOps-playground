# ТЗ: докеризация polyglot-микросервисного приложения (Junior+)

Исходный код сервисов уже готов (см. `frontend/`, `api/`, `worker/`). Твоя задача —
самостоятельно написать **Dockerfile для каждого сервиса** и **docker-compose.yml**,
которые их оркестрируют. Ниже — контракт, которому должно соответствовать решение,
и подсказки там, где это принципиально для безопасности/production-ready сборки.

---

## 1. Архитектура

| Сервис        | Технология              | Роль                                              |
|---------------|--------------------------|----------------------------------------------------|
| `frontend`    | Vite + React → статика   | Отдаёт SPA через Nginx, проксирует `/api` на `api` |
| `api`         | Python 3.12 / FastAPI     | REST API, читает/пишет в Postgres, кэширует в Redis |
| `worker`      | Node.js / TypeScript      | Фоновый обработчик очереди (BullMQ) через Redis     |
| `postgres_db` | PostgreSQL 16              | Основная БД                                        |
| `redis_cache` | Redis                      | Кэш + брокер очередей для worker                    |

---

## 2. Контракт переменных окружения

Код уже читает эти переменные — Dockerfile/compose должны их корректно прокидывать.

**api** (`.env.example` в `api/`):
```
DATABASE_URL=postgresql://<user>:<password>@postgres_db:5432/<db>
REDIS_URL=redis://redis_cache:6379/0
CORS_ORIGINS=["http://localhost"]
ENVIRONMENT=production
```

**worker** (`.env.example` в `worker/`):
```
REDIS_URL=redis://redis_cache:6379/0
QUEUE_NAME=default-queue
WORKER_CONCURRENCY=5
```

**frontend** (читается на этапе *сборки*, не в рантайме контейнера!):
```
VITE_API_BASE_URL=/api
```

**postgres_db** — стандартные переменные официального образа:
```
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_DB=...
```
Значения должны совпадать с тем, что подставлено в `DATABASE_URL` у `api`.

Проверочные эндпоинты уже реализованы:
- `GET /health` в api — проверяет одновременно Postgres (`SELECT 1`) и Redis (`PING`). Отличная база для healthcheck самого контейнера api.
- `GET /` в api — простой ответ, что сервис жив.

---

## 3. Требования к Dockerfile

### 3.1 `api/Dockerfile` (Python, multi-stage)
- **Этап 1 (builder):** базовый образ `python:3.12-slim` (или аналог), установить `build-essential`, `gcc`, а также **системные dev-заголовки**, нужные конкретно для `psycopg2` и `Pillow` (это не `psycopg2-binary` — собирается из исходников намеренно, чтобы ты потренировался на реальной C-зависимости). Собрать пакеты в wheel'ы (`pip wheel` или `pip install --user`).
- **Этап 2 (runtime):** чистый `python:3.12-slim`, копировать только собранные wheel'ы/пакеты из builder — **без** компиляторов и dev-заголовков. Обрати внимание: `psycopg2` в рантайме всё равно требует shared-библиотеку `libpq` (не dev-пакет, а runtime-версию) — без неё будет `ImportError` при старте.
- `WORKDIR`, `COPY` только нужных файлов (используй `.dockerignore`, чтобы не тащить `__pycache__`, `.venv`, `.env`).
- Непривилегированный `USER appuser` (создать через `useradd`/`adduser`, не root).
- `CMD`/`ENTRYPOINT` — запуск через `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- `EXPOSE 8000`.

### 3.2 `frontend/Dockerfile` (Node.js, multi-stage → Nginx)
- **Этап 1 (builder):** `node:20-alpine` (или LTS на выбор), `npm ci`, `npm run build` → результат в `/app/dist`.
- **Этап 2 (runtime):** `nginx:alpine`, скопировать `dist/` в `/usr/share/nginx/html`, подложить свой `nginx.conf` (см. п.5 — с проксированием `/api` → `api:8000`).
- Подумай: обязателен ли non-root для nginx alpine? (Он технически может слушать порт >1024 от непривилегированного пользователя — это бонусный челлендж, `nginx:alpine` уже содержит группу/юзера `nginx`.)
- `EXPOSE 80`.

### 3.3 `worker/Dockerfile` (Node.js, multi-stage)
- **Этап 1 (builder):** `node:20-alpine`, `npm ci`, `npm run build` (транспиляция TS → `dist/`).
- **Этап 2 (runtime):** чистый `node:20-alpine`, скопировать `package.json`, `package-lock.json` и `dist/` из builder, поставить **только** прод-зависимости и **обязательно** выполнить `npm prune --production` (или `npm ci --omit=dev`) — dev-зависимости (typescript, ts-node-dev, @types/*) не должны попасть в финальный слой.
- Непривилегированный пользователь (в `node:alpine` уже есть встроенный `USER node` — используй его).
- Никакого `EXPOSE` не требуется (сервис не слушает HTTP).
- `CMD ["node", "dist/index.js"]`.

---

## 4. Требования к docker-compose.yml

### 4.1 Сети (обязательна сегментация)

| Сеть           | Кто подключён                        |
|----------------|----------------------------------------|
| `frontend-net` | `frontend` (nginx), `api`               |
| `backend-net`  | `api`, `worker`, `redis_cache`          |
| `db-net`       | `api`, `postgres_db`                    |

Проверь себя: `frontend` не должен доставать ни до `postgres_db`, ни до `redis_cache` напрямую (только через `api`). `worker` не должен быть в `frontend-net`. `api` — единственный сервис, подключённый ко всем трём сетям (он мост между слоями).

### 4.2 Healthchecks и зависимости
- `postgres_db`: healthcheck на готовность БД принимать соединения (стандартная утилита из образа postgres).
- `redis_cache`: healthcheck на отклик сервера.
- `api`: `depends_on` на `postgres_db` и `redis_cache` с `condition: service_healthy` (не просто `service_started` — это частая ошибка Junior-уровня).
- `worker`: `depends_on` на `redis_cache` с `condition: service_healthy`.
- Опционально (бонус): собственный healthcheck у `api`, использующий `GET /health`.

### 4.3 Безопасность портов
- `postgres_db` и `redis_cache` — пробросить порты **только** на `127.0.0.1` (например `"127.0.0.1:5432:5432"`), не на `0.0.0.0`. Наружу (для браузера пользователя) должен смотреть только `frontend`.
- Подумай самостоятельно: нужен ли внешний проброс порта у `api` вообще, если `frontend` уже проксирует `/api` внутри `frontend-net`? Обоснуй свой выбор в комментарии к compose-файлу.

### 4.4 Ресурсы и restart policy
Ограничь `deploy.resources.limits` (cpus/memory) для каждого сервиса. Ориентировочные рамки для практики (можешь скорректировать под свою машину):

| Сервис        | CPU limit | Memory limit |
|---------------|-----------|--------------|
| `frontend`    | 0.2       | 128M         |
| `api`         | 0.5       | 512M         |
| `worker`      | 0.3       | 256M         |
| `postgres_db` | 1.0       | 512M         |
| `redis_cache` | 0.3       | 128M         |

Всем сервисам — `restart: unless-stopped`.

### 4.5 Volumes и конфиги
- `postgres_db`: именованный volume для `/var/lib/postgresql/data` (персистентность данных между рестартами).
- `frontend`: **не обязательно** пробрасывать `dist/` как volume, если он уже скопирован в образ на этапе сборки — но подложить свой `nginx.conf` через volume (или `COPY` в Dockerfile — выбери и обоснуй) нужно обязательно, т.к. дефолтный конфиг nginx:alpine не знает про проксирование `/api`.
- Напиши свой `nginx.conf` с как минимум: `location /` (отдача SPA, включая fallback на `index.html` для client-side роутинга) и `location /api/` (`proxy_pass http://api:8000/`).

---

## 5. Чек-лист самопроверки перед сдачей

- [ ] `docker compose up --build` поднимает все 5 сервисов без ошибок
- [ ] `curl http://localhost/` отдаёт HTML фронтенда, `curl http://localhost/api/health` → `{"status":"ok"}`
- [ ] `docker compose ps` показывает `healthy` у postgres и redis до того, как стартовали api/worker
- [ ] `docker exec` в контейнер api → `whoami` возвращает **не** root
- [ ] `docker exec` в контейнер worker → `whoami` возвращает **не** root
- [ ] финальный образ `api` не содержит `gcc`/`build-essential` (`docker exec api-container which gcc` → пусто)
- [ ] `psql`/`redis-cli` с хост-машины подключаются только через `127.0.0.1`, не через IP контейнера напрямую извне
- [ ] `docker inspect` подтверждает, что `frontend` не находится в `db-net`, а `worker` не находится в `frontend-net`
- [ ] размер финального образа `api` и `worker` заметно меньше, чем если бы ты не чистил dev-зависимости и билд-инструменты (сравни `docker images`)

---

Присылай Dockerfile'ы и compose — разберём построчно, как обычно.
