"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime configuration. Secrets must come from .env, never from source."""

    app_name: str = "Alpilab AI"
    app_env: str = "development"
    debug: bool = True
    ai_provider: str = "mock"
    ai_fallback_provider: str = "mock"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Alpilab AI"),
        app_env=os.getenv("APP_ENV", "development"),
        debug=_env_bool("DEBUG", True),
        ai_provider=os.getenv("AI_PROVIDER", "mock").strip().lower(),
        ai_fallback_provider=os.getenv("AI_FALLBACK_PROVIDER", "mock").strip().lower(),
    )
