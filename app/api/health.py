"""Health/status helpers for a future HTTP API."""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings


def health_payload() -> dict[str, Any]:
    """Return a simple health document (no network server started here)."""
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "ai_provider": settings.ai_provider,
        "phase": "foundation",
        "note": "HTTP API server not started in this phase.",
    }
