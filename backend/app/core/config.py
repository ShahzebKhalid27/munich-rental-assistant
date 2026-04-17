from functools import lru_cache

from pydantic import AnyUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Munich Rental Assistant API"
    environment: str = "dev"

    database_url: AnyUrl | None = None
    redis_url: AnyUrl | None = None

    media_storage_backend: str = "local"
    media_root: str = "./media"

    # Security
    secret_key: str = "change-me-before-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # LLM
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
