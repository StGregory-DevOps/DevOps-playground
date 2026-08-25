from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models import TaskStatus, TaskPriority


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, example="Fix login bug")
    description: Optional[str] = Field(None, example="Users can't login on mobile")
    priority: TaskPriority = TaskPriority.medium


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskStatusUpdate(BaseModel):
    """Используется воркером для обновления статуса через внутренний endpoint."""
    status: TaskStatus
