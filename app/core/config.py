"""Application configuration loaded from environment variables.

Secrets must never be committed. Copy `.env.example` to `.env` locally.
"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Runtime settings. Expand carefully — keep secrets out of code."""

    def __init__(self) -> None:
        self.app_name: str = os.getenv("APP_NAME", "Alpilab AI")
        self.environment: str = os.getenv("APP_ENV", "development")
        self.debug: bool = os.getenv("APP_DEBUG", "true").lower() in {
            "1",
            "true",
            "yes",
        }
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))
        # Provider name only — no API keys stored here in phase 1.
        self.ai_provider: str = os.getenv("AI_PROVIDER", "mock")
        # Database URLs are placeholders; no live DB in this phase.
        self.database_url: str = os.getenv(
            "DATABASE_URL", "sqlite:///./runtime_data/alpilab_ai.dev.db"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
