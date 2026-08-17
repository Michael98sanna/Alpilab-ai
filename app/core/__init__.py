"""Core configuration and shared utilities.

Secrets must come from environment variables / .env — never hard-coded.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Load .env if present (ignored by git). Safe no-op when file is missing.
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from the environment."""

    app_name: str = "Alpilab AI"
    environment: str = "development"
    ai_provider: str = "mock"
    # Database URL is optional in this foundation phase.
    database_url: str | None = None
    # Host/port for the optional HTTP API.
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Alpilab AI"),
        environment=os.getenv("ENVIRONMENT", "development"),
        ai_provider=os.getenv("AI_PROVIDER", "mock").lower(),
        database_url=os.getenv("DATABASE_URL") or None,
        api_host=os.getenv("API_HOST", "127.0.0.1"),
        api_port=int(os.getenv("API_PORT", "8000")),
    )
