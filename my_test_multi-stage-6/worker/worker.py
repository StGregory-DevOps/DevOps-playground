import time
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
INTERVAL = int(os.getenv("WORKER_INTERVAL", "10"))

engine = create_engine(DATABASE_URL)

def run():
    print("[worker] Starting inventory worker...", flush=True)
    while True:
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM items"))
                count = result.scalar()
                print(f"[worker] Items in DB: {count}", flush=True)
        except Exception as e:
            print(f"[worker] DB error: {e}", flush=True)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    run()
