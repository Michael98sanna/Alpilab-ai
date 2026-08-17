"""Application settings loaded from environment variables.

Never hard-code secrets. Copy `.env.example` to `.env` for local overrides.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Alpilab AI"
    app_env: str = "development"
    debug: bool = True

    # Provider selection — only "mock" is implemented in this phase.
    ai_provider: str = "mock"

    # Database URLs are placeholders; no ORM/session layer yet.
    database_url: str = "sqlite:///./runtime_data/alpilab_ai.db"

    # Future storage root for photos, schematics, annotated images.
    storage_root: str = "./runtime_data/storage"


@lru_cache
def get_settings() -> Settings:
    return Settings()
