import os
import json
import time
import logging
import signal
import sys

import redis
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("worker")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/analytics")
CLICK_QUEUE = "click_events"
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
POLL_TIMEOUT = int(os.getenv("POLL_TIMEOUT", "5"))  # seconds

running = True


def handle_signal(sig, frame):
    global running
    logger.info("Received signal %s, shutting down gracefully...", sig)
    running = False


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS click_events (
                id          BIGSERIAL PRIMARY KEY,
                short_code  VARCHAR(64)  NOT NULL,
                original_url TEXT        NOT NULL,
                clicked_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                raw_ts      DOUBLE PRECISION NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS click_stats (
                short_code   VARCHAR(64)  PRIMARY KEY,
                total_clicks BIGINT       NOT NULL DEFAULT 0,
                last_clicked TIMESTAMPTZ  NOT NULL DEFAULT NOW()
            );
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_click_events_code
                ON click_events (short_code);
        """)
    conn.commit()
    logger.info("Database schema ensured")


def insert_clicks(conn, events: list[dict]):
    rows = [(e["code"], e["original_url"], e["timestamp"]) for e in events]
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO click_events (short_code, original_url, raw_ts)
            VALUES %s
            """,
            rows,
        )
        # Upsert aggregated stats
        codes = list({e["code"] for e in events})
        for code in codes:
            count = sum(1 for e in events if e["code"] == code)
            cur.execute("""
                INSERT INTO click_stats (short_code, total_clicks, last_clicked)
                VALUES (%s, %s, NOW())
                ON CONFLICT (short_code) DO UPDATE
                    SET total_clicks = click_stats.total_clicks + EXCLUDED.total_clicks,
                        last_clicked = NOW()
            """, (code, count))
    conn.commit()
    logger.info("Persisted %d click events to PostgreSQL", len(events))


# ---------------------------------------------------------------------------
# Redis consumer
# ---------------------------------------------------------------------------

def parse_redis_url(url: str):
    # redis://host:port/db
    url = url.replace("redis://", "")
    host_part, db = url.rsplit("/", 1) if "/" in url else (url, "0")
    host, port = host_part.rsplit(":", 1) if ":" in host_part else (host_part, "6379")
    return host, int(port), int(db)


def main():
    host, port, db = parse_redis_url(REDIS_URL)
    r = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    conn = get_db_connection()
    ensure_schema(conn)

    logger.info("Worker started. Listening on queue '%s'...", CLICK_QUEUE)

    while running:
        try:
            # BLPOP blocks up to POLL_TIMEOUT seconds then returns None
            result = r.blpop(CLICK_QUEUE, timeout=POLL_TIMEOUT)
            if result is None:
                # Timeout — no events, loop again
                continue

            batch = []
            _, raw = result
            batch.append(json.loads(raw))

            # Drain up to BATCH_SIZE-1 more items without blocking
            for _ in range(BATCH_SIZE - 1):
                item = r.lpop(CLICK_QUEUE)
                if item is None:
                    break
                batch.append(json.loads(item))

            insert_clicks(conn, batch)

        except psycopg2.OperationalError as exc:
            logger.error("DB connection lost: %s. Reconnecting...", exc)
            time.sleep(3)
            try:
                conn = get_db_connection()
            except Exception as e:
                logger.error("Reconnect failed: %s", e)

        except redis.exceptions.ConnectionError as exc:
            logger.error("Redis connection lost: %s. Retrying...", exc)
            time.sleep(3)

        except Exception as exc:
            logger.exception("Unexpected error: %s", exc)
            time.sleep(1)

    logger.info("Worker stopped.")
    conn.close()
    sys.exit(0)


if __name__ == "__main__":
    main()
