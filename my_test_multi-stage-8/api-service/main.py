import os
import hashlib
import time
import json
import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
URL_TTL = int(os.getenv("URL_TTL", "86400"))  # 24h default
CLICK_QUEUE = "click_events"

redis_client: aioredis.Redis | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    logger.info("Connected to Redis")
    yield
    await redis_client.aclose()
    logger.info("Redis connection closed")


app = FastAPI(title="URL Shortener API", version="1.0.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ShortenRequest(BaseModel):
    url: HttpUrl
    alias: str | None = None


class ShortenResponse(BaseModel):
    short_url: str
    short_code: str
    original_url: str
    ttl_seconds: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def generate_short_code(url: str) -> str:
    timestamp = str(time.time()).encode()
    raw = f"{url}{timestamp}".encode()
    return hashlib.sha256(raw).hexdigest()[:7]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    try:
        await redis_client.ping()
        return {"status": "ok", "redis": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Redis unavailable: {exc}")


@app.get("/metrics")
async def metrics():
    info = await redis_client.info("stats")
    total_keys = await redis_client.dbsize()
    queue_len = await redis_client.llen(CLICK_QUEUE)
    return {
        "total_stored_urls": total_keys,
        "click_queue_length": queue_len,
        "redis_total_commands_processed": info.get("total_commands_processed"),
    }


@app.post("/shorten", response_model=ShortenResponse, status_code=201)
async def shorten_url(body: ShortenRequest):
    original = str(body.url)
    code = body.alias if body.alias else generate_short_code(original)

    exists = await redis_client.exists(f"url:{code}")
    if exists:
        raise HTTPException(status_code=409, detail=f"Alias '{code}' already taken")

    await redis_client.setex(f"url:{code}", URL_TTL, original)
    logger.info("Stored short code %s -> %s", code, original)

    return ShortenResponse(
        short_url=f"{BASE_URL}/r/{code}",
        short_code=code,
        original_url=original,
        ttl_seconds=URL_TTL,
    )


@app.get("/r/{code}")
async def redirect(code: str, response: Response):
    original = await redis_client.get(f"url:{code}")
    if not original:
        raise HTTPException(status_code=404, detail="Short URL not found or expired")

    event = {
        "code": code,
        "original_url": original,
        "timestamp": time.time(),
    }
    await redis_client.rpush(CLICK_QUEUE, json.dumps(event))
    logger.info("Click event queued for code %s", code)

    return RedirectResponse(url=original, status_code=302)


@app.get("/urls/{code}")
async def get_url_info(code: str):
    original = await redis_client.get(f"url:{code}")
    if not original:
        raise HTTPException(status_code=404, detail="Short URL not found")
    ttl = await redis_client.ttl(f"url:{code}")
    return {"code": code, "original_url": original, "ttl_remaining_seconds": ttl}
