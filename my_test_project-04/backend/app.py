import os
import json
import logging

from flask import Flask, jsonify, request
import psycopg2
import psycopg2.extras
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("moviehub")

app = Flask(__name__)

# --- Configuration is read entirely from environment variables ---
# This service expects the following env vars to be provided by Docker Compose:
#   POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
#   REDIS_HOST, REDIS_PORT
#   CACHE_TTL_SECONDS (optional, defaults to 60)
DB_HOST = os.environ["POSTGRES_HOST"]
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
DB_NAME = os.environ["POSTGRES_DB"]
DB_USER = os.environ["POSTGRES_USER"]
DB_PASSWORD = os.environ["POSTGRES_PASSWORD"]

REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
CACHE_TTL = int(os.environ.get("CACHE_TTL_SECONDS", 60))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


@app.route("/api/health")
def health():
    """Used by Docker healthcheck."""
    try:
        conn = get_db_connection()
        conn.close()
        redis_client.ping()
        return jsonify(status="ok"), 200
    except Exception as e:
        logger.error(f"Healthcheck failed: {e}")
        return jsonify(status="error", detail=str(e)), 503


@app.route("/api/movies")
def get_movies():
    genre = request.args.get("genre")
    cache_key = f"movies:{genre or 'all'}"

    cached = redis_client.get(cache_key)
    if cached:
        logger.info(f"Cache HIT for {cache_key}")
        return jsonify(json.loads(cached))

    logger.info(f"Cache MISS for {cache_key}")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if genre:
        cur.execute("SELECT * FROM movies WHERE genre = %s ORDER BY rating DESC", (genre,))
    else:
        cur.execute("SELECT * FROM movies ORDER BY rating DESC")
    movies = [dict(row) for row in cur.fetchall()]
    cur.close()
    conn.close()

    redis_client.setex(cache_key, CACHE_TTL, json.dumps(movies, default=str))
    return jsonify(movies)


@app.route("/api/movies/<int:movie_id>")
def get_movie(movie_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM movies WHERE id = %s", (movie_id,))
    movie = cur.fetchone()
    cur.close()
    conn.close()
    if not movie:
        return jsonify(error="Movie not found"), 404
    return jsonify(dict(movie))


@app.route("/api/movies/search")
def search_movies():
    q = request.args.get("q", "")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM movies WHERE title ILIKE %s ORDER BY rating DESC", (f"%{q}%",))
    movies = [dict(row) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(movies)


@app.route("/api/genres")
def get_genres():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT genre FROM movies ORDER BY genre")
    genres = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(genres)


@app.route("/api/movies", methods=["POST"])
def add_movie():
    data = request.get_json(force=True)
    required = ["title", "year", "genre", "rating"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify(error=f"Missing fields: {missing}"), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO movies (title, year, genre, rating, director, description)
           VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
        (   data["title"],
            data["year"],
            data["genre"],
            data["rating"],
            data.get("director", ""),
            data.get("description", "")
        )
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    # invalidate cache since dataset changed
    for key in redis_client.keys("movies:*"):
        redis_client.delete(key)

    return jsonify(id=new_id), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
