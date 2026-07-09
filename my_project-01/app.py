import os
import time
from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("POSTGRES_DB", "catalog")
DB_USER = os.environ.get("POSTGRES_USER", "catalog_user")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "catalog_pass")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = None


def get_engine():
    """Retry connecting to Postgres until it's ready (container startup race)."""
    global engine
    if engine is not None:
        return engine
    retries = 10
    while retries > 0:
        try:
            eng = create_engine(DATABASE_URL)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine = eng
            return engine
        except OperationalError:
            retries -= 1
            time.sleep(2)
    raise RuntimeError("Could not connect to the database after several retries")


def init_db():
    eng = get_engine()
    with eng.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                price NUMERIC(10, 2) NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0
            )
        """))
        conn.commit()


@app.route("/")
def index():
    eng = get_engine()
    with eng.connect() as conn:
        result = conn.execute(text("SELECT id, name, price, quantity FROM products ORDER BY id"))
        products = result.fetchall()
    return render_template("index.html", products=products)


@app.route("/add", methods=["POST"])
def add_product():
    name = request.form.get("name")
    price = request.form.get("price")
    quantity = request.form.get("quantity", 0)

    eng = get_engine()
    with eng.connect() as conn:
        conn.execute(
            text("INSERT INTO products (name, price, quantity) VALUES (:name, :price, :quantity)"),
            {"name": name, "price": price, "quantity": quantity},
        )
        conn.commit()
    return redirect(url_for("index"))


@app.route("/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    eng = get_engine()
    with eng.connect() as conn:
        conn.execute(text("DELETE FROM products WHERE id = :id"), {"id": product_id})
        conn.commit()
    return redirect(url_for("index"))


@app.route("/api/products")
def api_products():
    eng = get_engine()
    with eng.connect() as conn:
        result = conn.execute(text("SELECT id, name, price, quantity FROM products ORDER BY id"))
        products = [dict(row._mapping) for row in result]
    return jsonify(products)


@app.route("/health")
def health():
    try:
        eng = get_engine()
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
