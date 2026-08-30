"""
Background job(s) for LinkVault.

This module is imported by the RQ worker process. The API service
enqueues jobs by dotted path ("tasks.fetch_metadata"), so this file
must be importable from the worker's working directory.
"""
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.orm import sessionmaker, declarative_base

DB_HOST = os.getenv("DB_HOST", "mysql")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "linkvault")
DB_PASSWORD = os.getenv("DB_PASSWORD", "linkvault")
DB_NAME = os.getenv("DB_NAME", "linkvault")

DATABASE_URL = f"mysql+mysqldb://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=280)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


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


HEADERS = {"User-Agent": "LinkVaultBot/1.0 (+https://example.local)"}


def fetch_metadata(bookmark_id: int):
    """Fetch <title> and meta description for a saved URL and store them."""
    db = SessionLocal()
    try:
        bookmark = db.get(Bookmark, bookmark_id)
        if not bookmark:
            return

        bookmark.status = "processing"
        db.commit()

        try:
            response = requests.get(bookmark.url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            title_tag = soup.find("title")
            bookmark.title = title_tag.text.strip()[:512] if title_tag else bookmark.url

            description = ""
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                description = meta_desc["content"]
            else:
                og_desc = soup.find("meta", attrs={"property": "og:description"})
                if og_desc and og_desc.get("content"):
                    description = og_desc["content"]

            bookmark.description = re.sub(r"\s+", " ", description).strip()[:2000]
            bookmark.status = "done"
            bookmark.error_message = None

        except Exception as exc:  # noqa: BLE001 — a failed fetch should not crash the worker
            bookmark.status = "error"
            bookmark.error_message = str(exc)[:512]

        db.commit()
    finally:
        db.close()
