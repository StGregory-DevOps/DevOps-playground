"""
worker.py — фоновый воркер Task Tracker

Читает очередь task_queue из Redis (BLPOP — блокирующий pop).
Для каждого задания имитирует обработку и обновляет статус задачи
через внутренний API endpoint.

В реальном проекте здесь могут быть: отправка email, генерация отчёта,
вызов внешнего сервиса и т.д.
"""

import json
import logging
import os
import time

import redis
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WORKER] %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
API_URL = os.getenv("API_URL", "http://api:8000")
QUEUE_NAME = "task_queue"
BLOCK_TIMEOUT = 5  # секунд ожидания на BLPOP


def process_job(job: dict) -> None:
    task_id = job.get("task_id")
    action = job.get("action")

    log.info(f"Processing job: action={action}, task_id={task_id}")

    # Обновляем статус → in_progress
    _update_status(task_id, "in_progress")

    # Имитируем работу (парсинг, отправка, вычисление)
    time.sleep(2)

    # Готово — обновляем статус → done
    _update_status(task_id, "done")
    log.info(f"Task {task_id} marked as done.")


def _update_status(task_id: int, status: str) -> None:
    url = f"{API_URL}/tasks/{task_id}/status"
    try:
        resp = requests.patch(url, json={"status": status}, timeout=5)
        resp.raise_for_status()
    except requests.RequestException as e:
        log.error(f"Failed to update task {task_id} status to '{status}': {e}")


def main():
    log.info(f"Worker started. Connecting to Redis: {REDIS_URL}")
    r = redis.from_url(REDIS_URL, decode_responses=True)

    log.info(f"Listening on queue '{QUEUE_NAME}'...")
    while True:
        # BLPOP блокируется до BLOCK_TIMEOUT секунд, потом возвращает None
        result = r.blpop(QUEUE_NAME, timeout=BLOCK_TIMEOUT)
        if result is None:
            continue  # таймаут — проверяем снова

        _, raw = result
        try:
            job = json.loads(raw)
            process_job(job)
        except (json.JSONDecodeError, KeyError) as e:
            log.error(f"Invalid job payload: {raw!r} — {e}")


if __name__ == "__main__":
    main()
