"""Device Context schemas for V0.6 repair device tracking."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


DeviceSource = Literal["adb", "alpilab_check", "3utools", "manual", "unknown"]
ConnectionType = Literal["usb", "wifi", "bluetooth", "manual", "unknown"]


class DetectedDevice(BaseModel):
    """A device physically connected to the PC and identified, but not yet
    associated with a RepairSession."""

    id: str
    brand: str | None = None
    model: str | None = None
    variant: str | None = None
    serial_number: str | None = None
    imei: str | None = None
    connection_type: ConnectionType = "unknown"
    source: DeviceSource = "unknown"
    detected_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def display_name(self) -> str:
        parts = [p for p in (self.brand, self.model) if p]
        return " ".join(parts) if parts else self.id


class DeviceContext(BaseModel):
    """The single device explicitly associated with a RepairSession by the
    user.  All fields are optional so that a session can start without any
    device and be enriched later."""

    id: str
    brand: str | None = None
    model: str | None = None
    variant: str | None = None
    serial_number: str | None = None
    imei: str | None = None
    color: str | None = None
    storage: str | None = None
    battery_health: str | None = None
    connection_type: ConnectionType = "unknown"
    source: DeviceSource = "unknown"
    detected_at: datetime | None = None
    associated_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def display_name(self) -> str:
        parts = [p for p in (self.brand, self.model) if p]
        return " ".join(parts) if parts else self.id

    @classmethod
    def from_detected(
        cls, detected: DetectedDevice, *, associated_at: datetime | None = None
    ) -> DeviceContext:
        """Promote a DetectedDevice to a DeviceContext upon user association."""
        return cls(
            id=detected.id,
            brand=detected.brand,
            model=detected.model,
            variant=detected.variant,
            serial_number=detected.serial_number,
            imei=detected.imei,
            connection_type=detected.connection_type,
            source=detected.source,
            detected_at=detected.detected_at,
            associated_at=associated_at,
            metadata=dict(detected.metadata),
        )
