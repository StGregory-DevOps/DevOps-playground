from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.cache import redis_client
from app.database import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    redis_client.ping()
    return {"status": "ok"}
