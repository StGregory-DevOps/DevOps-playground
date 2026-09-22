from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class MonitorCreate(BaseModel):
    name: str
    url: HttpUrl
    interval_seconds: int = 60


class MonitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    interval_seconds: int
    is_active: bool
    created_at: datetime
    last_checked_at: datetime | None


class CheckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    checked_at: datetime
    success: bool
    status_code: int | None
    response_time_ms: float | None
    error_message: str | None


class UptimeOut(BaseModel):
    monitor_id: int
    period_hours: int
    total_checks: int
    successful_checks: int
    uptime_percent: float
