from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/monitors", tags=["checks"])


def _ensure_monitor_exists(db: Session, monitor_id: int) -> None:
    if not crud.get_monitor(db, monitor_id):
        raise HTTPException(status_code=404, detail="Monitor not found")


@router.get("/{monitor_id}/checks", response_model=list[schemas.CheckOut])
def get_checks(monitor_id: int, limit: int = 50, db: Session = Depends(get_db)):
    _ensure_monitor_exists(db, monitor_id)
    return crud.list_checks(db, monitor_id, limit)


@router.get("/{monitor_id}/uptime", response_model=schemas.UptimeOut)
def get_uptime(monitor_id: int, hours: int = 24, db: Session = Depends(get_db)):
    _ensure_monitor_exists(db, monitor_id)
    return crud.compute_uptime(db, monitor_id, hours)
