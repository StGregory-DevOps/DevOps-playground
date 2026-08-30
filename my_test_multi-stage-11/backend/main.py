"""
LinkVault API — backend service.

Handles CRUD for bookmarks and enqueues background jobs (via Redis/RQ)
that fetch page metadata (title, description) for each new link.
The actual fetching happens in the separate `worker` service.
"""
import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, ConfigDict
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.orm import sessionmaker, declarative_base
import redis
from rq import Queue

# --- Configuration (all values come from environment variables) ---
DB_HOST = os.getenv("DB_HOST", "mysql")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "linkvault")
DB_PASSWORD = os.getenv("DB_PASSWORD", "linkvault")
DB_NAME = os.getenv("DB_NAME", "linkvault")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

DATABASE_URL = f"mysql+mysqldb://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=280)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
task_queue = Queue("metadata", connection=redis_conn)


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), nullable=False)
    note = Column(String(512), nullable=True)
    title = Column(String(512), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(
        Enum("pending", "processing", "done", "error", name="status_enum"),
        default="pending",
    )
    error_message = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BookmarkCreate(BaseModel):
    url: HttpUrl
    note: Optional[str] = None


class BookmarkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    note: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime


app = FastAPI(title="LinkVault API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/bookmarks", response_model=List[BookmarkOut])
def list_bookmarks():
    db = SessionLocal()
    try:
        return db.query(Bookmark).order_by(Bookmark.created_at.desc()).all()
    finally:
        db.close()


@app.post("/api/bookmarks", response_model=BookmarkOut, status_code=201)
def create_bookmark(payload: BookmarkCreate):
    db = SessionLocal()
    try:
        bookmark = Bookmark(url=str(payload.url), note=payload.note, status="pending")
        db.add(bookmark)
        db.commit()
        db.refresh(bookmark)

        # Hand off metadata fetching to the worker service via the Redis queue
        task_queue.enqueue("tasks.fetch_metadata", bookmark.id)

        return bookmark
    finally:
        db.close()


@app.get("/api/bookmarks/{bookmark_id}", response_model=BookmarkOut)
def get_bookmark(bookmark_id: int):
    db = SessionLocal()
    try:
        bookmark = db.get(Bookmark, bookmark_id)
        if not bookmark:
            raise HTTPException(status_code=404, detail="Bookmark not found")
        return bookmark
    finally:
        db.close()


@app.delete("/api/bookmarks/{bookmark_id}", status_code=204)
def delete_bookmark(bookmark_id: int):
    db = SessionLocal()
    try:
        bookmark = db.get(Bookmark, bookmark_id)
        if not bookmark:
            raise HTTPException(status_code=404, detail="Bookmark not found")
        db.delete(bookmark)
        db.commit()
    finally:
        db.close()
