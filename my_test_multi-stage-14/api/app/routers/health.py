from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from ..database import engine

router = APIRouter()


@router.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail={"status": "error", "database": "down"})

    return {"status": "ok", "database": "up"}
