# PixelForge

Сервис обработки изображений: загрузка картинки → фоновая генерация превью
200×200 и ч/б версии → отдача через Nginx.

## Стек

- **Nginx** — реверс-прокси, статика, отдача файлов из volume
- **Node.js / Express** — API (загрузка, список, статус)
- **Node.js / sharp** — воркер обработки изображений
- **PostgreSQL** — метаданные + очередь задач (`SELECT ... FOR UPDATE SKIP LOCKED`)

## Архитектура

```
[browser] → [nginx] ──/──────────→ статика (frontend/)
                     ──/api/─────→ [api] ──→ [postgres] ←── [worker] (poll + sharp)
                     ──/uploads/─→ shared volume (напрямую, без Node)
                     ──/processed/→ shared volume (напрямую, без Node)
```

## API

- `POST /api/images` — загрузить изображение (`multipart/form-data`, поле `image`)
- `GET /api/images` — список всех изображений со статусами
- `GET /api/images/:id` — статус и имена файлов одного изображения
- `GET /health` — healthcheck для API

## Как запустить

Docker-часть (`Dockerfile`×2, `docker-compose.yml`) ещё не написана — см. `TASK.md`.

После того как она будет готова:

```bash
docker compose up -d --build
```

Открыть `http://localhost` (порт — тот, что укажешь в `docker-compose.yml`).

## Структура

```
pixelforge/
├── frontend/       # статика для nginx
├── nginx/          # nginx.conf
├── api/            # Express API
├── worker/         # воркер на sharp
├── db/init.sql     # схема БД
├── .env.example
├── TASK.md         # ТЗ
└── TRACKER.md      # чеклист прогресса
```
