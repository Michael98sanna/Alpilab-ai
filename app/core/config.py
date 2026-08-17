"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass, field


def _parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    """Runtime settings for Alpilab AI."""

    ai_provider: str = "mock"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]
    )

    @classmethod
    def from_env(cls) -> "Settings":
        extra_origins = _parse_csv(os.getenv("CORS_ORIGINS", ""))
        base_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]
        merged = base_origins + [o for o in extra_origins if o not in base_origins]
        return cls(
            ai_provider=os.getenv("AI_PROVIDER", "mock").strip().lower(),
            debug=os.getenv("DEBUG", "false").strip().lower() in {"1", "true", "yes"},
            host=os.getenv("HOST", "0.0.0.0").strip(),
            port=int(os.getenv("PORT", "8000")),
            cors_origins=merged,
        )


settings = Settings.from_env()
