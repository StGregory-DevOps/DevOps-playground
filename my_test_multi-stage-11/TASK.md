# ТЗ: LinkVault — Docker Compose практика

## Что это

LinkVault — менеджер закладок. Пользователь сохраняет ссылку,
бэкенд кладёт её в MySQL и ставит задачу в очередь (Redis),
воркер в фоне скачивает страницу и вытаскивает title/description,
фронтенд (статика за Nginx) опрашивает API и показывает карточки
со статусом: pending → processing → done/error.

Весь код приложения уже готов (папки `frontend/`, `backend/`,
`worker/`, `mysql/`, `nginx/`). Твоя задача — написать Dockerfile
для сервисов, которым он нужен, и `docker-compose.yml`, который
свяжет всё вместе.

## Сервисы

### 1. mysql
- Официальный образ `mysql:8` — свой Dockerfile не нужен.
- Смонтировать `mysql/init.sql` в `/docker-entrypoint-initdb.d/`.
- Именованный volume для `/var/lib/mysql` (данные не должны
  теряться при `docker compose down`).
- Переменные окружения: `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`,
  `MYSQL_USER`, `MYSQL_PASSWORD` (через `env_file`, из `.env`).
- Healthcheck: `mysqladmin ping -h localhost -u root -p$MYSQL_ROOT_PASSWORD`.
- Порт наружу не пробрасывать — нужен только внутри сети.

### 2. redis
- Официальный образ `redis:7-alpine`.
- Healthcheck: `redis-cli ping`.
- Порт наружу не пробрасывать.

### 3. backend (FastAPI)
- Свой Dockerfile, multi-stage build.
- ⚠️ `mysqlclient` — C-расширение. Для сборки нужны build-зависимости
  (`default-libmysqlclient-dev`, `build-essential`, `pkg-config`)
  в builder-стадии; в финальном слое оставь только рантайм-либу
  (например `default-mysql-client` или `libmariadb3`, в зависимости
  от базового образа) — так финальный образ останется компактным.
- Непривилегированный пользователь для запуска приложения.
- CMD: `uvicorn main:app --host 0.0.0.0 --port 8000`.
- Порт 8000 — только внутри сети (наружу не публикуем, к нему идёт
  Nginx).
- `depends_on`: mysql (`service_healthy`), redis (`service_healthy`).
- Healthcheck: `curl -f http://localhost:8000/api/health` (curl нужно
  доставить в финальный образ, либо проверяй через встроенный
  `python -c "import urllib.request..."`, если хочешь обойтись без
  curl).
- Переменные окружения: `DB_HOST`, `DB_PORT`, `DB_USER`,
  `DB_PASSWORD`, `DB_NAME`, `REDIS_HOST`, `REDIS_PORT`.

### 4. worker
- Свой Dockerfile, тот же принцип multi-stage/C-зависимостей, что
  и у backend (тоже использует `mysqlclient`).
- Непривилегированный пользователь.
- CMD: `python worker.py`.
- Без HTTP-healthcheck (это фоновый процесс) — по желанию можно
  усложнить и добавить проверку, что процесс жив.
- `depends_on`: mysql (`service_healthy`), redis (`service_healthy`).
- Те же переменные окружения, что у backend (кроме тех, что ему не
  нужны).

### 5. nginx
- Официальный образ `nginx:alpine` — свой Dockerfile не обязателен,
  но можно сделать свой, чтобы скопировать статику и конфиг внутрь
  образа (тоже хорошая практика).
- Смонтировать/скопировать `frontend/` в `/usr/share/nginx/html`.
- Смонтировать/скопировать `nginx/nginx.conf` в
  `/etc/nginx/conf.d/default.conf`.
- Единственный сервис, чей порт пробрасывается наружу: `80 → 8080`
  (или любой свободный порт на хосте).
- `depends_on`: backend.

## Сеть

Все сервисы — в одной user-defined bridge-сети, чтобы обращаться
друг к другу по имени сервиса (`mysql`, `redis`, `backend`).

## Переменные окружения

Используй `env_file: .env` для каждого сервиса, которому нужен
конфиг/секреты — не `${VAR}`-интерполяцию. Пример лежит в
`.env.example`, скопируй его в `.env`.

## Что проверить в конце

- `docker compose up --build` поднимает всё без ошибок.
- На `http://localhost:8080` видно форму и пустой список.
- Добавление ссылки создаёт карточку со статусом «В очереди», через
  несколько секунд статус меняется на «Готово» и подтягиваются
  title/description.
- `docker compose down && docker compose up` — данные в MySQL
  сохранились (volume работает).
- Образы backend и worker — многослойные (builder + рантайм), без
  лишних dev-пакетов в финальном слое.
