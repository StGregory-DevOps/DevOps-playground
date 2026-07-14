import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
    REDIS_DB = int(os.environ.get("REDIS_DB", 0))

    RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", 10))
    CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", 300))
    BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
