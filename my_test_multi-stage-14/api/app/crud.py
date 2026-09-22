from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas


def create_monitor(db: Session, payload: schemas.MonitorCreate) -> models.Monitor:
    monitor = models.Monitor(
        name=payload.name,
        url=str(payload.url),
        interval_seconds=payload.interval_seconds,
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return monitor


def list_monitors(db: Session) -> list[models.Monitor]:
    return db.query(models.Monitor).order_by(models.Monitor.created_at.desc()).all()


def get_monitor(db: Session, monitor_id: int) -> models.Monitor | None:
    return db.query(models.Monitor).filter(models.Monitor.id == monitor_id).first()


def delete_monitor(db: Session, monitor: models.Monitor) -> None:
    db.delete(monitor)
    db.commit()


def list_checks(db: Session, monitor_id: int, limit: int = 50) -> list[models.Check]:
    return (
        db.query(models.Check)
        .filter(models.Check.monitor_id == monitor_id)
        .order_by(models.Check.checked_at.desc())
        .limit(limit)
        .all()
    )


def compute_uptime(db: Session, monitor_id: int, hours: int = 24) -> dict:
    since = datetime.utcnow() - timedelta(hours=hours)
    total = (
        db.query(func.count(models.Check.id))
        .filter(models.Check.monitor_id == monitor_id, models.Check.checked_at >= since)
        .scalar()
    )
    successful = (
        db.query(func.count(models.Check.id))
        .filter(
            models.Check.monitor_id == monitor_id,
            models.Check.checked_at >= since,
            models.Check.success.is_(True),
        )
        .scalar()
    )
    uptime = (successful / total * 100) if total else 0.0
    return {
        "monitor_id": monitor_id,
        "period_hours": hours,
        "total_checks": total,
        "successful_checks": successful,
        "uptime_percent": round(uptime, 2),
    }
