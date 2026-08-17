"""Future bridge to Alpilab Check.

Alpilab Check is a separate Windows application. This connector is the only
place Alpilab AI should ever learn about Check data.

Transport is intentionally unspecified: a later implementation may use HTTP,
a local file drop, or a Hub-mediated channel. This module does not import
Check internals and does not assume its database or UI.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from app.models import Device, DiagnosticTest


class CheckConnectorInfo(BaseModel):
    """Metadata about the bridge itself, not about Check internals."""

    name: str
    available: bool
    is_mock: bool
    transport: str = Field(
        description="How this connector would talk to Check, e.g. http, file, hub."
    )


class DeviceIdentityPayload(BaseModel):
    """Neutral identity document that Check (or a technician) can supply."""

    brand: str
    model: str
    model_code: str | None = None
    imei: str | None = None
    serial_number: str | None = None
    color: str | None = None
    storage_gb: int | None = None
    os_name: str | None = None
    os_version: str | None = None


class DiagnosticSnapshotPayload(BaseModel):
    """Opaque diagnostic export. `tests` is already mapped to the AI contract;
    `raw` may carry extra keys that AI must treat as unknown.
    """

    tests: list[dict[str, Any]] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class AlpilabCheckConnector(ABC):
    """Integration port. Implementations must not spawn Check or run commands."""

    @abstractmethod
    def get_info(self) -> CheckConnectorInfo:
        """Describe this connector."""

    @abstractmethod
    def is_available(self) -> bool:
        """True if a live transport is reachable. Mock returns True."""

    @abstractmethod
    def import_device_identity(self, payload: DeviceIdentityPayload) -> Device:
        """Map a Check-originated (or manual) payload onto the Device contract."""

    @abstractmethod
    def import_diagnostic_snapshot(
        self,
        session_id: Any,
        payload: DiagnosticSnapshotPayload,
    ) -> list[DiagnosticTest]:
        """Map a snapshot onto DiagnosticTest records. Unknown keys stay in raw_payload."""


class MockAlpilabCheckConnector(AlpilabCheckConnector):
    """In-memory stub. Does not contact Alpilab Check or the filesystem."""

    def get_info(self) -> CheckConnectorInfo:
        return CheckConnectorInfo(
            name="alpilab-check-mock",
            available=True,
            is_mock=True,
            transport="none",
        )

    def is_available(self) -> bool:
        return True

    def import_device_identity(self, payload: DeviceIdentityPayload) -> Device:
        return Device(
            brand=payload.brand,
            model=payload.model,
            model_code=payload.model_code,
            imei=payload.imei,
            serial_number=payload.serial_number,
            color=payload.color,
            storage_gb=payload.storage_gb,
            os_name=payload.os_name,
            os_version=payload.os_version,
            notes="Imported via MockAlpilabCheckConnector (no live Check link).",
        )

    def import_diagnostic_snapshot(
        self,
        session_id: Any,
        payload: DiagnosticSnapshotPayload,
    ) -> list[DiagnosticTest]:
        tests: list[DiagnosticTest] = []
        for item in payload.tests:
            name = str(item.get("name") or "unspecified")
            tests.append(
                DiagnosticTest(
                    session_id=session_id,
                    name=name,
                    category=str(item.get("category") or "unknown"),
                    source="alpilab_check",
                    result_summary=item.get("result_summary"),
                    raw_payload={"item": item, "snapshot_raw": payload.raw},
                )
            )
        return tests
