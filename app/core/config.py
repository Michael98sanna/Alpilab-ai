"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    """Runtime settings. Secrets must come from the environment, never from source."""

    app_name: str = "Alpilab AI"
    app_env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    ai_provider: str = "mock"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


def _load_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "8000")),
        ai_provider=os.getenv("AI_PROVIDER", "mock"),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return _load_settings()
