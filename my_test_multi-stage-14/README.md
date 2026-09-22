# PulseCheck

Учебный pet-проект: мини-сервис мониторинга доступности сайтов (свой маленький
аналог UptimeRobot). Добавляешь URL — воркер периодически его пингует, история
проверок и процент аптайма доступны через API.

## Стек

- **api** — FastAPI, SQLAlchemy, MySQL (CRUD мониторов, история проверок, аптайм %)
- **worker** — Python, бесконечный цикл опроса (без Redis/очереди — просто polling таблицы `monitors`)
- **nginx** — reverse proxy перед api (фронтенда в проекте нет)
- **MySQL 8** — хранение мониторов и результатов проверок

## Функциональность

- `POST /monitors` — добавить сайт для мониторинга (`name`, `url`, `interval_seconds`)
- `GET /monitors` — список мониторов
- `GET /monitors/{id}` — один монитор
- `DELETE /monitors/{id}` — удалить
- `GET /monitors/{id}/checks?limit=50` — история проверок
- `GET /monitors/{id}/uptime?hours=24` — процент аптайма за период
- `GET /health` — статус api + подключения к MySQL (503, если БД недоступна)

Воркер каждые `TICK_SECONDS` секунд ищет мониторы, которым "пора" проверяться
(`last_checked_at` + `interval_seconds` <= сейчас), стучится на их URL, пишет
результат (код ответа, время отклика, успех/провал) в таблицу `checks`.

## Запуск локально без Docker (для разработки/проверки)

Понадобится локальный MySQL (например временный контейнер `mysql:8`).

```bash
# api
cd api
pip install -r requirements.txt
cp ../.env.example .env   # поправить DB_HOST=localhost для локального запуска
uvicorn app.main:app --reload --port 8000

# worker (в отдельном терминале)
cd worker
pip install -r requirements.txt
cp ../.env.example .env
python main.py
```

## Дальше — докеризация

Исходники готовы, `nginx/nginx.conf` тоже уже написан. Задача — два Dockerfile'а
(builder-стадия в обоих уже есть) и `docker-compose.yml` с нуля. Подробное ТЗ — `TASK.md`.
