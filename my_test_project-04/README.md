# CineVault — DevOps Handoff

Разработчики закончили приложение. Твоя задача как DevOps-инженера — упаковать это
в Docker и поднять весь стек через docker-compose. Ничего из Docker-инфраструктуры
(Dockerfile, docker-compose.yml, .env) в проекте нет специально — это твоя работа.

## Что уже готово (трогать не нужно)

moviehub/
├── backend/
│   ├── app.py            # Flask REST API
│   ├── requirements.txt  # зависимости
│   └── init_db.sql       # схема + сид-данные для Postgres
├── nginx/
│   ├── nginx.conf         # reverse proxy + отдача статики
│   └── html/
│       ├── index.html
│       ├── style.css
│       └── script.js
└── README.md
## Сервисы, которые нужно поднять

| Сервис    | Образ / база                | Роль                                              |
|-----------|------------------------------|----------------------------------------------------|
| nginx   | нужно собрать свой Dockerfile | reverse proxy на /api/, отдаёт статику из nginx/html |
| backend | нужно собрать свой Dockerfile | Flask API, слушает 5000 внутри контейнера        |
| db      | postgres:15-alpine          | хранит таблицу movies, инициализируется init_db.sql |
| redis   | redis:7-alpine               | кэш ответов /api/movies (TTL настраивается через env) |

## Переменные окружения, которые ожидает backend (обязательны — иначе упадёт при старте)

| Переменная           | Назначение                          | Пример значения |
|----------------------|---------------------------------------|------------------|
| POSTGRES_HOST      | хост базы (имя сервиса в compose)     | db             |
| POSTGRES_PORT      | порт Postgres (опционально, default 5432) | 5432       |
| POSTGRES_DB        | имя базы                              | moviehub       |
| POSTGRES_USER      | пользователь БД                       | moviehub_user  |
| POSTGRES_PASSWORD  | пароль БД                             | *(придумай сам)* |
| REDIS_HOST         | хост Redis (имя сервиса в compose)    | redis          |
| REDIS_PORT         | порт Redis (опционально, default 6379)| 6379           |
| CACHE_TTL_SECONDS  | TTL кэша в секундах (опционально)     | 60             |

Эти же значения (POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD) нужно передать
и в сам контейнер db — official postgres-образ поднимает базу именно по ним.

## Что нужно сделать тебе

1. **.env** в корне проекта — со всеми переменными из таблицы выше.
2. **backend/Dockerfile** — образ на базе python, ставит requirements.txt,
   запускает app.py (продумай, стоит ли использовать gunicorn вместо flask run
   для продакшн-подобного запуска).
3. **nginx/Dockerfile** — образ на базе nginx, копирует nginx.conf и html/
   на нужные места внутри контейнера.
4. **docker-compose.yml**, который поднимает все 4 сервиса и учитывает:
   - depends_on с healthcheck-условиями (backend не должен стартовать раньше,
     чем БД готова принимать соединения);
   - volume для персистентности данных Postgres между перезапусками;
   - монтирование init_db.sql в /docker-entrypoint-initdb.d/ контейнера Postgres
     (официальный образ сам выполнит его при первом старте);
   - проброс наружу только порта nginx (80) — остальные сервисы наружу торчать
     не должны;
   - отдельную docker-сеть для всего стека.

## Как проверить, что всё работает

- curl http://localhost/ → отдаётся index.html и работает интерфейс.
- curl http://localhost/api/movies → JSON со списком фильмов.
- curl http://localhost/api/health → {"status": "ok"} (если Postgres/Redis не
  видны backend'у — вернёт 503, это специально сделано для проверки healthcheck).
- После docker compose down и docker compose up данные в Postgres должны
  сохраниться (проверка volume).
