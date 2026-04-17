from functools import lru_cache
from pydantic import BaseSettings, AnyUrl


class Settings(BaseSettings):
    app_name: str = "Munich Rental Assistant API"
    environment: str = "dev"

    database_url: AnyUrl | None = None
    redis_url: AnyUrl | None = None

    media_storage_backend: str = "local"  # or "s3" später
    media_root: str = "./media"  # für lokale Entwicklung

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
