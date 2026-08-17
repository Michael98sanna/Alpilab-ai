"""Device identity model — shared contract for AI / Check / Hub."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Device(BaseModel):
    """Smartphone / tablet under repair."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    brand: str
    model: str
    identifier: str | None = Field(
        default=None,
        description="IMEI, serial, or other lab identifier when available.",
    )
    color: str | None = None
    storage_gb: int | None = None
    os_version: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
