import json

from redis import Redis

from app.config import settings

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

CACHE_TTL_SECONDS = 30
CACHE_KEY_ITEMS = "items:list"


def get_cached_items():
    cached = redis_client.get(CACHE_KEY_ITEMS)
    return json.loads(cached) if cached else None


def set_cached_items(items: list[dict]):
    redis_client.set(CACHE_KEY_ITEMS, json.dumps(items), ex=CACHE_TTL_SECONDS)


def invalidate_items_cache():
    redis_client.delete(CACHE_KEY_ITEMS)
