import os
import json
import time

from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import redis

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "taskdb")
DB_USER = os.getenv("DB_USER", "taskuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "taskpass")

REDIS_HOST = os.getenv("REDIS_HOST", "cache")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

CACHE_TTL = int(os.getenv("CACHE_TTL", 30))


def get_db_connection(retries=5, delay=2):
    last_err = None
    for _ in range(retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
            )
            return conn
        except psycopg2.OperationalError as e:
            last_err = e
            time.sleep(delay)
    raise last_err


def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            done BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


@app.route("/tasks", methods=["GET"])
def list_tasks():
    r = get_redis_client()
    cached = r.get("tasks:all")
    if cached:
        return jsonify(source="cache", tasks=json.loads(cached))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, title, done, created_at FROM tasks ORDER BY id;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    tasks = [dict(row, created_at=str(row["created_at"])) for row in rows]
    r.setex("tasks:all", CACHE_TTL, json.dumps(tasks))

    return jsonify(source="db", tasks=tasks)


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json(force=True)
    title = data.get("title")
    if not title:
        return jsonify(error="title is required"), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title) VALUES (%s) RETURNING id;", (title,))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    get_redis_client().delete("tasks:all")

    return jsonify(id=new_id, title=title, done=False), 201


@app.route("/tasks/<int:task_id>/done", methods=["PATCH"])
def mark_done(task_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET done = TRUE WHERE id = %s;", (task_id,))
    updated = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    if updated == 0:
        return jsonify(error="task not found"), 404

    get_redis_client().delete("tasks:all")
    return jsonify(id=task_id, done=True)

init_db()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
