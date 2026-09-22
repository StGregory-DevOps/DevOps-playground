from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from database import Base


class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False)
    interval_seconds = Column(Integer, nullable=False, default=60)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checked_at = Column(DateTime, nullable=True)


class Check(Base):
    __tablename__ = "checks"

    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False, index=True)
    checked_at = Column(DateTime, default=datetime.utcnow, index=True)
    success = Column(Boolean, nullable=False)
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
