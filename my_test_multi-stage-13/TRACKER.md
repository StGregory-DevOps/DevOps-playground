# PixelForge — Трекер прогресса

## Nginx
- [ ] Dockerfile / базовый образ `nginx:alpine` + COPY конфига
- [ ] `location /` — отдаёт статику фронтенда
- [ ] `location /api/` — проксирует на `api`
- [ ] `location /uploads/` и `/processed/` — alias на shared volume
- [ ] Проверено вручную через браузер

## API (Node.js)
- [ ] Dockerfile (multi-stage: builder → production)
- [ ] non-root user
- [ ] `.dockerignore`
- [ ] Healthcheck (`/health` эндпоинт уже есть в коде)
- [ ] Загрузка файла реально сохраняется в `UPLOAD_DIR`

## Worker (Node.js + sharp)
- [ ] Dockerfile (multi-stage)
- [ ] Разобрался с `sharp` на выбранном базовом образе (alpine/slim) — записать вывод `npm install`
- [ ] non-root user
- [ ] Проверен размер финального образа (`docker images`)
- [ ] Воркер реально забирает `pending`-записи и переводит их в `done`

## PostgreSQL
- [ ] Healthcheck (`pg_isready`)
- [ ] Volume для персистентности данных (`pg-data`)
- [ ] `db/init.sql` подключён через `/docker-entrypoint-initdb.d`
- [ ] Таблица `images` создаётся автоматически при первом старте

## docker-compose.yml
- [ ] Все сервисы используют `env_file`
- [ ] `depends_on: condition: service_healthy` для `api` и `worker` → `postgres`
- [ ] Общие volumes `uploads` и `processed` подключены к `api` + `worker` + `nginx`
- [ ] Именованная сеть
- [ ] `docker compose up -d --build` поднимает всё без ошибок с нуля

## Финальная проверка
- [ ] Полный цикл: загрузка → обработка → скачивание превью — работает end-to-end
- [ ] `docker compose down -v` корректно всё чистит
- [ ] README дополнен инструкцией запуска
- [ ] Запушено на GitHub
