"""Application settings loaded from environment variables.

No secrets are hardcoded. Copy `.env.example` to `.env` for local overrides.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


@dataclass(frozen=True)
class Settings:
    """Runtime configuration. Safe defaults for local development."""

    app_name: str = "Alpilab AI"
    environment: str = "development"
    ai_provider: str = "mock"
    # Database URLs are placeholders — no live DB required in this phase.
    database_url: str = "sqlite:///./runtime_data/alpilab_ai.db"
    # Future cloud storage root (local path for now).
    storage_root: str = "./runtime_data/storage"
    # Safety: never allow arbitrary command execution from config.
    allow_dangerous_hub_actions: bool = False
    require_confirmation_for_dangerous_actions: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=_env("APP_NAME", "Alpilab AI"),
            environment=_env("APP_ENV", "development"),
            ai_provider=_env("AI_PROVIDER", "mock"),
            database_url=_env(
                "DATABASE_URL", "sqlite:///./runtime_data/alpilab_ai.db"
            ),
            storage_root=_env("STORAGE_ROOT", "./runtime_data/storage"),
            allow_dangerous_hub_actions=_env(
                "ALLOW_DANGEROUS_HUB_ACTIONS", "false"
            ).lower()
            in {"1", "true", "yes"},
            require_confirmation_for_dangerous_actions=_env(
                "REQUIRE_CONFIRMATION_FOR_DANGEROUS_ACTIONS", "true"
            ).lower()
            in {"1", "true", "yes"},
        )


def get_settings() -> Settings:
    return Settings.from_env()
