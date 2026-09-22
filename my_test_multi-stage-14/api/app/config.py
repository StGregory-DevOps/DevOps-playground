from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_host: str = "mysql"
    db_port: int = 3306
    db_user: str = "pulsecheck"
    db_password: str = "pulsecheck"
    db_name: str = "pulsecheck"
    cors_origin: str = "*"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    class Config:
        env_prefix = ""


settings = Settings()
