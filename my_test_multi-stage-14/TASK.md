# ТЗ: докеризация PulseCheck

Уровень: Junior / Junior+. Код приложения (api, worker) готов — задача обернуть
его в Docker так, как это обычно просят на реальных заданиях.

## Состав системы (4 сервиса)

| Сервис    | Что это                                         | Собирается из образа |
|-----------|--------------------------------------------------|------------------------|
| `nginx`   | reverse proxy перед api (порт 80)                | официальный образ, без сборки — конфиг уже лежит в `nginx/nginx.conf` |
| `api`     | FastAPI, CRUD мониторов + история + аптайм (порт 8000) | свой Dockerfile |
| `worker`  | Python-скрипт, крутит бесконечный цикл опроса URL | свой Dockerfile |
| `mysql`   | MySQL 8                                          | официальный образ, без сборки |

## Что нужно сделать

### 1. `api/Dockerfile`

- Builder-стадия уже написана: ставит зависимости через `pip install --user`
  (кладёт пакеты в `/root/.local`) и копирует `app/`.
- Runtime-стадия — с нуля:
  - тот же базовый образ (`python:3.12-slim`);
  - скопировать `/root/.local` из builder в домашнюю директорию **непривилегированного** пользователя
    (создать его самому, например `appuser`) и прописать `ENV PATH=...`, чтобы установленные
    пакеты были видны;
  - скопировать `app/` из builder;
  - **не под root** — создать пользователя и переключиться на него до `CMD`;
  - слушает порт 8000, `CMD` — `uvicorn app.main:app --host 0.0.0.0 --port 8000`;
  - `GET /health` уже реализован в коде (отдаёт 503, если MySQL недоступна) — используй
    его для `HEALTHCHECK` (в Dockerfile или в compose — на твой выбор, но объясни себе, почему).

### 2. `worker/Dockerfile`

- Builder-стадия аналогична api.
- Runtime: тот же подход (непривилегированный пользователь, копирование `/root/.local`,
  копирование кода), но `CMD` — `python main.py` (у воркера нет HTTP-порта, `EXPOSE` не нужен).
- **Отдельный вопрос на подумать**: у воркера нет HTTP-эндпоинта, как у api. Значит
  `HEALTHCHECK` через `curl`/`wget` тут не сделать напрямую. Варианты — вообще без
  healthcheck (как мы делали с Redis в одном из прошлых проектов), либо проверка, что
  процесс жив (`pgrep -f main.py` или похожее). Выбери сам и будь готов обосновать выбор.

### 3. `docker-compose.yml` (в корне проекта)

- Четыре сервиса: `nginx`, `api`, `worker`, `mysql`.
- `api` и `worker` — `build:` из своих Dockerfile. `nginx` и `mysql` — готовые образы,
  без `build:`.
- `nginx`: `image: nginx:alpine`, конфиг из `nginx/nginx.conf` подключить через `volumes`
  (смонтировать поверх дефолтного `/etc/nginx/conf.d/default.conf`, в режиме `:ro`).
- `mysql`: `image: mysql:8`, переменные из `.env` (`MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`,
  `MYSQL_USER`, `MYSQL_PASSWORD` — это фиксированные имена, которые ждёт сам образ),
  volume для `/var/lib/mysql`, чтобы данные не терялись между перезапусками.
- Healthcheck для `mysql` — через `mysqladmin ping` (разберись, какие флаги ему нужны).
- `api` и `worker` должны стартовать только когда `mysql` реально готова —
  `depends_on` с `condition: service_healthy`.
- `nginx` — `depends_on: api` (без обязательного условия healthy, просто порядок запуска).
- Переменные — через `env_file:`, не через `${VAR}` в `environment:`.
- Сети: `mysql`, `api`, `worker` — в одной сети (бэкенд-часть); `api` и `nginx` — в другой
  (чтобы nginx мог резолвить `api` по имени сервиса). `worker` наружу вообще не торчит
  никаким портом — ему это не нужно, он ничего не принимает, только сам стучится наружу.
- Наружу пробросить только `nginx` (`8080:80` например). `api`, `worker`, `mysql` —
  без `ports:`, только внутри docker-сети.

## Проверка результата

1. `docker compose up --build`
2. `docker compose ps` — все сервисы `healthy`/`running`.
3. `curl -X POST http://localhost:8080/monitors -H "Content-Type: application/json" -d '{"name": "example", "url": "https://example.com", "interval_seconds": 30}'`
4. Подождать ~30-40 секунд, затем `curl http://localhost:8080/monitors/1/checks` —
   должна появиться хотя бы одна запись с результатом проверки.
5. `curl http://localhost:8080/monitors/1/uptime` — должен вернуться процент аптайма.
6. Убить `mysql` (`docker compose stop mysql`) — `api`-healthcheck должен упасть
   в unhealthy, а не зависнуть молча.

## Что не нужно делать

- Не нужны миграции (Alembic) — используется `Base.metadata.create_all()` при старте
  (см. комментарий в коде, почему это ок только для pet-проекта).
- Не нужен Redis/очередь — воркер работает через polling самой таблицы `monitors`
  (см. `worker/main.py`), это осознанный выбор для этого масштаба задачи.
