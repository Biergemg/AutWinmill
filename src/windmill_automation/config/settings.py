from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str | None = None
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_HOST: str | None = None
    DB_PORT: int = 5432
    DB_NAME: str | None = None
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL

        required = [self.DB_USER, self.DB_PASSWORD, self.DB_HOST, self.DB_NAME]
        if all(required):
            return (
                f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        raise RuntimeError(
            "Missing DB configuration. Set DATABASE_URL or DB_USER/DB_PASSWORD/DB_HOST/DB_NAME"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
