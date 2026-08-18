# library-api

Junior+ Multi-Stage Build practice project.

## Services

| Service  | Image base  | Port  | Role                              |
|----------|-------------|-------|-----------------------------------|
| `api`    | python:3.12 | 8000  | FastAPI REST, CRUD books/readers/rentals |
| `worker` | python:3.12 | —     | Checks overdue rentals every 30s, writes to Redis |
| `db`     | postgres:16 | 5432  | PostgreSQL, stores all data       |
| `cache`  | redis:7     | 6379  | Redis, worker writes overdue keys |

## Endpoints

### Books
- `POST   /books/`               — create book
- `GET    /books/`               — list all books
- `GET    /books/{id}`           — get book by id
- `DELETE /books/{id}`           — delete book

### Readers
- `POST   /readers/`             — create reader
- `GET    /readers/`             — list all readers
- `GET    /readers/{id}`         — get reader by id

### Rentals
- `POST   /rentals/`             — rent a book (sets book.available=False)
- `GET    /rentals/`             — list all rentals
- `PATCH  /rentals/{id}/return`  — return book (sets book.available=True)
- `GET    /rentals/overdue/`     — list overdue rentals (API query)

## Worker behavior

Every 30 seconds the worker:
1. Queries PostgreSQL for rentals where `due_date < NOW()` and `returned_at IS NULL`
2. Writes each overdue rental to Redis as `overdue:rental:{id}`
3. Updates `overdue:count` and `overdue:last_check` keys in Redis

## Docker keys to practice

- Multi-Stage Build: builder stage (venv в `/opt/venv`) + runtime stage
- Non-root USER в обоих сервисах (api и worker)
- `depends_on` + `healthcheck` для db и cache
- `env_file: .env` для всех сервисов
- `restart: unless-stopped`

## Quick test

```bash
# Create a book
curl -X POST http://localhost:8000/books/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Clean Code", "author": "Robert Martin", "year": 2008}'

# Create a reader
curl -X POST http://localhost:8000/readers/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Ivan Petrenko", "email": "ivan@example.com"}'

# Rent the book (due_date in the past = overdue)
curl -X POST http://localhost:8000/rentals/ \
  -H "Content-Type: application/json" \
  -d '{"book_id": 1, "reader_id": 1, "due_date": "2024-01-01T00:00:00Z"}'

# Check overdue via API
curl http://localhost:8000/rentals/overdue/

# Check overdue keys in Redis
docker compose exec cache redis-cli keys "overdue:*"
```
