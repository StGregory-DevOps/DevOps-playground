import time
from datetime import datetime

import requests
from sqlalchemy import func, or_, text

from config import settings
from database import Base, SessionLocal, engine
from models import Check, Monitor


def get_due_monitors(db):
    # interval_seconds -- это колонка, а не число, поэтому "now - interval" нельзя
    # посчитать в Python: сравнение должно выполняться в самой БД.
    seconds_since_last_check = func.timestampdiff(
        text("SECOND"), Monitor.last_checked_at, func.now()
    )
    return (
        db.query(Monitor)
        .filter(Monitor.is_active.is_(True))
        .filter(
            or_(
                Monitor.last_checked_at.is_(None),
                seconds_since_last_check >= Monitor.interval_seconds,
            )
        )
        .all()
    )


def check_monitor(monitor: Monitor) -> Check:
    start = time.monotonic()
    try:
        response = requests.get(monitor.url, timeout=settings.request_timeout_seconds)
        elapsed_ms = (time.monotonic() - start) * 1000
        return Check(
            monitor_id=monitor.id,
            checked_at=datetime.utcnow(),
            success=response.status_code < 400,
            status_code=response.status_code,
            response_time_ms=round(elapsed_ms, 2),
            error_message=None,
        )
    except requests.RequestException as exc:
        elapsed_ms = (time.monotonic() - start) * 1000
        return Check(
            monitor_id=monitor.id,
            checked_at=datetime.utcnow(),
            success=False,
            status_code=None,
            response_time_ms=round(elapsed_ms, 2),
            error_message=str(exc)[:500],
        )


def run_tick():
    db = SessionLocal()
    try:
        due = get_due_monitors(db)
        for monitor in due:
            check = check_monitor(monitor)
            db.add(check)
            monitor.last_checked_at = check.checked_at
            db.add(monitor)
            db.commit()
            status = "OK" if check.success else "FAIL"
            print(f"[{check.checked_at.isoformat()}] {monitor.name} -> {status} "
                  f"({check.status_code}, {check.response_time_ms} ms)", flush=True)
    finally:
        db.close()


def main():
    # На реальном проде тут были бы миграции (Alembic), для pet-проекта — create_all
    Base.metadata.create_all(bind=engine)
    print(f"PulseCheck worker started, tick={settings.tick_seconds}s", flush=True)
    while True:
        run_tick()
        time.sleep(settings.tick_seconds)


if __name__ == "__main__":
    main()
