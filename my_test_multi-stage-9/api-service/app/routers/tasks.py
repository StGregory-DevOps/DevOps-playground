import json
from typing import List

import redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db, settings
from app.models import Task, TaskStatus
from app.schemas import TaskCreate, TaskOut, TaskStatusUpdate, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Redis клиент
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

CACHE_TTL = 60  # секунд


def _cache_key(task_id: int) -> str:
    return f"task:{task_id}"


def _invalidate_cache(task_id: int):
    redis_client.delete(_cache_key(task_id))
    # Также инвалидируем список
    redis_client.delete("tasks:all")


# ── CREATE ──────────────────────────────────────────────────────────────────

@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)

    # Кладём в очередь Redis для воркера
    job = {"task_id": task.id, "action": "process_new_task"}
    redis_client.lpush("task_queue", json.dumps(job))

    redis_client.delete("tasks:all")  # инвалидируем список
    return task


# ── READ ALL ─────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    cached = redis_client.get("tasks:all")
    if cached:
        # Возвращаем из кэша — десериализуем вручную через Pydantic
        return [TaskOut(**t) for t in json.loads(cached)]

    tasks = db.query(Task).order_by(Task.created_at.desc()).all()
    result = [TaskOut.model_validate(t) for t in tasks]

    redis_client.setex(
        "tasks:all",
        CACHE_TTL,
        json.dumps([t.model_dump(mode="json") for t in result]),
    )
    return result


# ── READ ONE ─────────────────────────────────────────────────────────────────

@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    cached = redis_client.get(_cache_key(task_id))
    if cached:
        return TaskOut(**json.loads(cached))

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    out = TaskOut.model_validate(task)
    redis_client.setex(_cache_key(task_id), CACHE_TTL, out.model_dump_json())
    return out


# ── UPDATE ───────────────────────────────────────────────────────────────────

@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    _invalidate_cache(task_id)
    return task


# ── DELETE ───────────────────────────────────────────────────────────────────

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    _invalidate_cache(task_id)


# ── INTERNAL: воркер обновляет статус ────────────────────────────────────────

@router.patch("/{task_id}/status", response_model=TaskOut)
def update_task_status(
    task_id: int,
    payload: TaskStatusUpdate,
    db: Session = Depends(get_db),
):
    """Внутренний endpoint — вызывается worker-service."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = payload.status
    db.commit()
    db.refresh(task)
    _invalidate_cache(task_id)
    return task
