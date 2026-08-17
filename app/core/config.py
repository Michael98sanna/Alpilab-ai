"""Application settings loaded from environment variables.

Secrets must live in `.env` (gitignored). This module never hard-codes keys.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. All secrets come from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Alpilab AI"
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"

    ai_provider: str = "mock"

    # Placeholders for future providers. Empty on purpose.
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None

    database_url: str | None = None

    phase: str = Field(
        default="foundation",
        description="Development phase label. Not a feature flag.",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def is_development(self) -> bool:
        return self.environment.lower() in {"development", "dev", "local"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
