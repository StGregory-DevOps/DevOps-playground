# Blog API

REST API для блога на Node.js (Express) с PostgreSQL в качестве базы данных
и Redis в качестве слоя кэширования. Nginx используется как reverse proxy
перед приложением.

## Стек

- Node.js 20 + Express
- PostgreSQL 16
- Redis 7
- Nginx (reverse proxy)

## Эндпоинты

| Метод  | Путь              | Описание                        |
|--------|-------------------|----------------------------------|
| GET    | /health           | Проверка состояния БД и Redis   |
| GET    | /api/posts        | Список всех постов (кэшируется) |
| GET    | /api/posts/:id    | Пост по id (кэшируется)         |
| POST   | /api/posts        | Создать пост                    |
| PUT    | /api/posts/:id    | Обновить пост                   |
| DELETE | /api/posts/:id    | Удалить пост                    |

## Локальный запуск без Docker

\\\bash
npm install
cp .env.example .env
# указать в .env адреса своей локальной БД и Redis (localhost)
npm run dev
\\\

## Запуск через Docker

Dockerfile и docker-compose.yml — самостоятельное задание.
