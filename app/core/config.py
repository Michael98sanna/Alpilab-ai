"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings for Alpilab AI."""

    ai_provider: str = "mock"
    debug: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            ai_provider=os.getenv("AI_PROVIDER", "mock").strip().lower(),
            debug=os.getenv("DEBUG", "false").strip().lower() in {"1", "true", "yes"},
        )


settings = Settings.from_env()
