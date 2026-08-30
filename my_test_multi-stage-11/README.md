# LinkVault

Менеджер закладок с автоматическим подтягиванием title/description
для сохранённых ссылок. Учебный pet-проект для практики Docker Compose:
MySQL + Redis + очередь задач + воркер + Nginx как reverse proxy.

## Как это работает

1. Пользователь добавляет ссылку через веб-интерфейс.
2. Backend (FastAPI) сохраняет запись в MySQL со статусом `pending`
   и ставит задачу в очередь Redis.
3. Worker забирает задачу из очереди, скачивает страницу, вытаскивает
   `<title>` и meta description, обновляет запись в MySQL
   (`processing` → `done`/`error`).
4. Frontend раз в 3 секунды опрашивает API и обновляет карточки.

## Структура репозитория

```
frontend/     — статический SPA (HTML/CSS/JS), отдаётся Nginx
backend/      — FastAPI: REST API + постановка задач в очередь
worker/       — RQ-воркер: скачивание метаданных страниц
mysql/        — init.sql — схема таблицы bookmarks
nginx/        — nginx.conf — reverse proxy + отдача статики
.env.example  — пример переменных окружения
TASK.md       — ТЗ на Dockerfile/docker-compose.yml
```

## Что нужно сделать самому

Dockerfile для backend/worker и docker-compose.yml в этом репозитории
нет специально — это и есть практика. Требования по каждому сервису
смотри в `TASK.md`.

## Запуск (после того как напишешь Dockerfile/compose)

```bash
cp .env.example .env
# отредактируй .env при необходимости
docker compose up --build
```

Приложение будет доступно на `http://localhost:8080` (или на том
порту, который укажешь в docker-compose.yml).
