"""Schemas for Alpilab Hub capability contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PCStatus(BaseModel):
    online: bool
    hostname: str | None = None
    os: str | None = None
    hub_version: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=_utcnow)


class HubActionResult(BaseModel):
    """Result of a Hub capability call.

    ``mock=True`` means no real PC action was performed.
    """

    success: bool
    action: str
    message: str
    mock: bool = True
    data: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False
