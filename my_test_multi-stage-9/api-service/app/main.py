from fastapi import FastAPI

from app.database import Base, engine
from app.routers import tasks

# Создаём таблицы при старте (в продакшне — миграции через Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Task Tracker API",
    description="REST API для управления задачами. Redis-кэш + очередь для воркера.",
    version="1.0.0",
)

app.include_router(tasks.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
