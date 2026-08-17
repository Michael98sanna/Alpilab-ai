"""Hub request/response types."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


HUB_CAPABILITIES = (
    "open_application",
    "close_application",
    "capture_microscope",
    "capture_thermal_camera",
    "read_multimeter",
    "read_power_supply",
    "get_pc_status",
)


class HubResult(BaseModel):
    """Outcome of a Hub call. Mocks set executed=False and is_mock=True."""

    capability: str
    ok: bool
    executed: bool
    is_mock: bool
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    at: datetime = Field(default_factory=_utcnow)


class ApplicationActionRequest(BaseModel):
    """Ask Hub to open or close a known application.

    `application` is a logical name (e.g. "3utools"), never a raw command.
    Arbitrary executable paths are rejected by the mock.
    """

    application: str = Field(min_length=1)
    confirmed: bool = False


class PcStatus(BaseModel):
    reachable: bool
    hostname: str | None = None
    is_mock: bool = True
    capabilities: list[str] = Field(default_factory=lambda: list(HUB_CAPABILITIES))
    notes: str | None = None
