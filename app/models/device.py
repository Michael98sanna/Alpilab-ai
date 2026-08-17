"""Device identity shared across Alpilab AI, Check, and Hub."""

from __future__ import annotations

from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DeviceIdentifierType(str, Enum):
    IMEI = "imei"
    SERIAL = "serial"
    UNKNOWN = "unknown"


class Device(BaseModel):
    """A smartphone (or similar device) under diagnosis or repair."""

    id: UUID = Field(default_factory=uuid4)
    brand: str
    model: str
    identifier: str | None = None
    identifier_type: DeviceIdentifierType = DeviceIdentifierType.UNKNOWN
    os_name: str | None = None
    os_version: str | None = None
    color: str | None = None
    storage_gb: int | None = None
    board_revision: str | None = None
    notes: str | None = None
