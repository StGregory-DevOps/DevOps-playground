# inventory-api

REST API сервис управления інвентарем на FastAPI + MySQL.

## Стек

- **FastAPI** — REST API
- **MySQL 8.0** — база даних
- **SQLAlchemy + PyMySQL** — ORM і драйвер для MySQL
- **Worker** — фоновий сервіс, що кожні 10 секунд виводить кількість товарів у БД
- **Docker Multi-Stage Build** — окремі Dockerfile для `api` і `worker`
- **Docker Compose** — оркестрація трьох сервісів

---

## Структура проекту

```
inventory-api/
├── api/
│   ├── Dockerfile          ← пишеш сам
│   ├── requirements.txt
│   └── main.py
├── worker/
│   ├── Dockerfile          ← пишеш сам
│   ├── requirements.txt
│   └── worker.py
├── docker-compose.yml      ← пишеш сам
├── .env
└── README.md
```

---

## Твоє завдання

### 1. `api/Dockerfile`
- Multi-stage: `builder` → `production`
- Base image: `python:3.12-slim`
- Builder: створює venv `/opt/venv`, встановлює залежності
- Production: копіює venv з builder, копіює `main.py`
- Запуск: `uvicorn main:app --host 0.0.0.0 --port 8000`

### 2. `worker/Dockerfile`
- Multi-stage: `builder` → `production`
- Аналогічно `api/Dockerfile`
- Запуск: `python worker.py`

### 3. `docker-compose.yml`
Три сервіси:

**`db`** — `mysql:8.0`
- Змінні з `.env`
- Named volume: `mysql_data`
- `healthcheck` через `mysqladmin ping`

**`api`**
- Build: `./api`
- Port: `8000:8000`
- `DATABASE_URL` з `.env`
- `depends_on` db з `condition: service_healthy`

**`worker`**
- Build: `./worker`
- `DATABASE_URL` з `.env`
- `WORKER_INTERVAL=10`
- `depends_on` db з `condition: service_healthy`

---

## Запуск

```bash
docker compose up --build
```

---

## Перевірка

```bash
# Створити товар
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "quantity": 5, "price": 999.99}'

# Список товарів
curl http://localhost:8000/items

# Отримати товар за id
curl http://localhost:8000/items/1

# Видалити товар
curl -X DELETE http://localhost:8000/items/1
```

Worker у логах кожні 10 секунд виводить:
```
[worker] Items in DB: 3
```

---

## .env

```
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=inventory
MYSQL_USER=appuser
MYSQL_PASSWORD=apppassword
DATABASE_URL=mysql+pymysql://appuser:apppassword@db/inventory
```

> ⚠️ `.env` не комітити в git — додай у `.gitignore`
