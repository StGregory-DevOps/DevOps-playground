"""
Entrypoint that starts an RQ worker listening on the "metadata" queue.

Run with: python worker.py
(This is what the container's CMD should invoke.)
"""
import os

import redis
from rq import Worker, Queue

import tasks  # noqa: F401 — imported so RQ can resolve "tasks.fetch_metadata" jobs

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

if __name__ == "__main__":
    conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    queue = Queue("metadata", connection=conn)
    worker = Worker([queue], connection=conn)
    worker.work()
