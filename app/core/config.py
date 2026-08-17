"""Core application utilities: configuration and settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Runtime settings loaded from environment variables / .env.

    Never put secrets in source code. Use .env locally (git-ignored).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Alpilab AI"
    app_env: str = "development"
    debug: bool = True

    # AI
    ai_provider: str = "mock"

    # Database (not wired yet — placeholders for future)
    database_url: str = "sqlite:///./runtime_data/alpilab_ai.db"

    # Security placeholders (auth not implemented in this phase)
    # SECRET_KEY must never be committed; only referenced via env.
    secret_key: str = "change-me-in-env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
