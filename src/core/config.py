from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "taskmanager_db"
    postgres_user: str = "taskmanager"
    postgres_password: str = "taskmanager"
    postgres_ssl: bool = False

    secret_key: str = "change-me-in-production-use-a-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    api_title: str = "Task Manager API"
    api_version: str = "1.0.0"
    cors_origins: list[str] = ["*"]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def ssl_connect_args(self) -> dict:
        return {"ssl": "require"} if self.postgres_ssl else {}


settings = Settings()
