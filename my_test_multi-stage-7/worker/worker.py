import os
import time
import redis
from datetime import datetime, timezone
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.environ["REDIS_URL"]
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 30))

engine = create_engine(DATABASE_URL)
r = redis.from_url(REDIS_URL, decode_responses=True)


def check_overdue():
    now = datetime.now(timezone.utc)
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT
                    rentals.id,
                    books.title,
                    readers.name,
                    readers.email,
                    rentals.due_date
                FROM rentals
                JOIN books   ON rentals.book_id   = books.id
                JOIN readers ON rentals.reader_id = readers.id
                WHERE rentals.due_date < :now
                  AND rentals.returned_at IS NULL
            """),
            {"now": now}
        )
        rows = result.fetchall()

    if not rows:
        print(f"[{now.isoformat()}] No overdue rentals.", flush=True)
        return

    for row in rows:
        rental_id, title, reader_name, email, due_date = row
        key = f"overdue:rental:{rental_id}"
        value = (
            f"OVERDUE | Book: '{title}' | Reader: {reader_name} ({email}) "
            f"| Due: {due_date}"
        )
        r.set(key, value)
        print(f"[{now.isoformat()}] {value}", flush=True)

    r.set("overdue:last_check", now.isoformat())
    r.set("overdue:count", len(rows))
    print(f"[{now.isoformat()}] Total overdue: {len(rows)}", flush=True)


if __name__ == "__main__":
    print("Worker started. Checking every %d seconds..." % CHECK_INTERVAL, flush=True)
    while True:
        try:
            check_overdue()
        except Exception as e:
            print(f"[ERROR] {e}", flush=True)
        time.sleep(CHECK_INTERVAL)
