from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql://postgres:postgres@postgres_db:5432/appdb"
    redis_url: str = "redis://redis_cache:6379/0"
    cors_origins: list[str] = ["*"]


settings = Settings()
