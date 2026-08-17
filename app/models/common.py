"""Shared types for domain models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum


class SourceSystem(str, Enum):
    """Where a record originated. Used as a stable contract across products."""

    ALPILAB_AI = "alpilab_ai"
    ALPILAB_CHECK = "alpilab_check"
    ALPILAB_HUB = "alpilab_hub"
    MANUAL = "manual"
    UNKNOWN = "unknown"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
