from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/monitors", tags=["monitors"])


@router.get("", response_model=list[schemas.MonitorOut])
def list_monitors(db: Session = Depends(get_db)):
    return crud.list_monitors(db)


@router.post("", response_model=schemas.MonitorOut, status_code=201)
def create_monitor(payload: schemas.MonitorCreate, db: Session = Depends(get_db)):
    return crud.create_monitor(db, payload)


@router.get("/{monitor_id}", response_model=schemas.MonitorOut)
def get_monitor(monitor_id: int, db: Session = Depends(get_db)):
    monitor = crud.get_monitor(db, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return monitor


@router.delete("/{monitor_id}", status_code=204)
def delete_monitor(monitor_id: int, db: Session = Depends(get_db)):
    monitor = crud.get_monitor(db, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    crud.delete_monitor(db, monitor)
