from flask import Blueprint, request, jsonify, redirect
from app.database import db
from app.models import Link, Click
from app.redis_client import redis_client
from app.utils import generate_short_code
from app.config import Config

bp = Blueprint("routes", __name__)


def is_rate_limited(ip: str) -> bool:
    key = f"ratelimit:{ip}"
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, 60)
    return current > Config.RATE_LIMIT_PER_MINUTE


@bp.route("/api/shorten", methods=["POST"])
def shorten():
    ip = request.remote_addr
    if is_rate_limited(ip):
        return jsonify({"error": "Rate limit exceeded"}), 429

    data = request.get_json(silent=True) or {}
    original_url = data.get("url")
    if not original_url:
        return jsonify({"error": "url is required"}), 400

    code = generate_short_code()
    while Link.query.filter_by(short_code=code).first():
        code = generate_short_code()

    link = Link(short_code=code, original_url=original_url)
    db.session.add(link)
    db.session.commit()

    return jsonify({
        "short_url": f"{Config.BASE_URL}/{code}",
        "code": code
    }), 201


@bp.route("/<code>", methods=["GET"])
def go_to_url(code):
    cached_url = redis_client.get(f"link:{code}")

    if cached_url:
        original_url = cached_url
        link = Link.query.filter_by(short_code=code).first()
    else:
        link = Link.query.filter_by(short_code=code).first()
        if not link:
            return jsonify({"error": "Not found"}), 404
        original_url = link.original_url
        redis_client.setex(f"link:{code}", Config.CACHE_TTL_SECONDS, original_url)

    if link:
        click = Click(link_id=link.id, ip_address=request.remote_addr)
        db.session.add(click)
        db.session.commit()

    return redirect(original_url, code=302)


@bp.route("/api/stats/<code>", methods=["GET"])
def stats(code):
    link = Link.query.filter_by(short_code=code).first()
    if not link:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "code": link.short_code,
        "original_url": link.original_url,
        "created_at": link.created_at.isoformat(),
        "total_clicks": len(link.clicks)
    })


@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

