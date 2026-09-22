from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_host: str = "mysql"
    db_port: int = 3306
    db_user: str = "pulsecheck"
    db_password: str = "pulsecheck"
    db_name: str = "pulsecheck"

    # как часто воркер опрашивает таблицу monitors на предмет "пора проверять"
    tick_seconds: int = 5
    # таймаут HTTP-запроса к целевому URL
    request_timeout_seconds: int = 5

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
