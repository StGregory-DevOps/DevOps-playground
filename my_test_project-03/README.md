# LinkTrack

Сервис сокращения ссылок с подсчётом переходов и кэшированием через Redis.

## Стек

- Python 3.11 / Flask
- PostgreSQL — хранение ссылок и статистики переходов
- Redis — кэш редиректов + rate limiting
- Nginx — reverse proxy
- Docker / docker-compose

## Структура проекта

linktrack/
├── app/
│   ├── __init__.py      # application factory
│   ├── config.py        # конфигурация из переменных окружения
│   ├── database.py      # инициализация SQLAlchemy
│   ├── redis_client.py  # подключение к Redis
│   ├── models.py        # модели Link, Click
│   └── routes.py        # эндпоинты API
├── run.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
└── nginx/
    └── nginx.conf
## Запуск

1. Заполнить .env (см. пример ниже)
2. Собрать и запустить:
  
   docker-compose up --build
   
3. Приложение доступно на http://localhost:8000

## Переменные окружения (.env)

| Переменная | Описание |
|---|---|
| POSTGRES_USER | пользователь БД |
| POSTGRES_PASSWORD | пароль БД |
| POSTGRES_DB | имя базы данных |
| DATABASE_URL | полная строка подключения для приложения |
| REDIS_HOST | хост Redis (имя сервиса в compose) |
| REDIS_PORT | порт Redis |
| RATE_LIMIT_PER_MINUTE | лимит запросов на создание ссылок с одного IP |
| BASE_URL | базовый URL для формирования коротких ссылок |

## API

| Метод | Путь | Описание |
|---|---|---|
| POST | /api/shorten | создать короткую ссылку ({"url": "..."}) |
| GET | /<code> | редирект на оригинальный URL |
| GET | /api/stats/<code> | статистика: дата создания, кол-во переходов |
| GET | /health | healthcheck приложения |

## Примечания

- Redis кэширует соответствие код → URL на CACHE_TTL_SECONDS, чтобы не ходить в Postgres на каждый редирект.
- Rate limiting реализован через Redis-счётчик с TTL в 60 секунд.
