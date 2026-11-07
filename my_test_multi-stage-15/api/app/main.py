"""LinkWatch API: accepts URLs to check and returns results stored in Redis."""

import os
import time
import uuid
from functools import lru_cache
from typing import Annotated

import redis
from fastapi import Depends, FastAPI, HTTPException
from pydantic import AnyHttpUrl, BaseModel

QUEUE_KEY = "linkwatch:queue"
JOB_PREFIX = "linkwatch:job:"
JOB_TTL_SECONDS = int(os.getenv("JOB_TTL_SECONDS", "3600"))

app = FastAPI(title="LinkWatch API", version="1.0.0")


class CheckRequest(BaseModel):
    url: AnyHttpUrl


@lru_cache
def get_redis() -> redis.Redis:
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return redis.Redis.from_url(url, decode_responses=True)


RedisDep = Annotated[redis.Redis, Depends(get_redis)]


@app.get("/health")
def health(r: RedisDep) -> dict[str, str]:
    try:
        r.ping()
    except redis.RedisError as exc:
        raise HTTPException(status_code=503, detail="redis unavailable") from exc
    return {"status": "ok"}


@app.post("/checks", status_code=202)
def create_check(body: CheckRequest, r: RedisDep) -> dict[str, str]:
    job_id = uuid.uuid4().hex
    key = f"{JOB_PREFIX}{job_id}"
    job = {
        "url": str(body.url),
        "status": "pending",
        "created_at": str(int(time.time())),
    }
    r.hset(key, mapping=job)
    r.expire(key, JOB_TTL_SECONDS)
    r.lpush(QUEUE_KEY, job_id)
    return {"id": job_id, "status": "pending"}


@app.get("/checks/{job_id}")
def get_check(job_id: str, r: RedisDep) -> dict[str, str]:
    data = r.hgetall(f"{JOB_PREFIX}{job_id}")
    if not data:
        raise HTTPException(status_code=404, detail="check not found")
    return {"id": job_id, **data}
