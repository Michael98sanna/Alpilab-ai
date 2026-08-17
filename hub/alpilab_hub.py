"""Alpilab Hub — conceptual Windows PC bridge (interfaces + mock only).

Hub will eventually sit on a lab Windows PC and mediate between the
cloud and local hardware/software (microscope, thermal camera,
multimeter, power supply, 3uTools, etc.).

SECURITY:
- No arbitrary shell execution.
- No remote shell.
- Dangerous actions require permissions + explicit confirmation.
- This module must never call subprocess for user-supplied commands.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.core.security import evaluate_action


class HubPCStatus(BaseModel):
    online: bool
    hostname: str | None = None
    os_name: str | None = None
    hub_version: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class HubCaptureResult(BaseModel):
    success: bool
    source: str
    message: str
    storage_path: str | None = None
    is_mock: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class HubReadingResult(BaseModel):
    success: bool
    instrument: str
    value: float | str | None = None
    unit: str | None = None
    message: str
    is_mock: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class HubActionResult(BaseModel):
    success: bool
    action: str
    message: str
    requires_confirmation: bool = False
    is_mock: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class AlpilabHub(ABC):
    """Contract for the future Windows Hub service."""

    name: str = "alpilab_hub"

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_pc_status(self) -> HubPCStatus:
        raise NotImplementedError

    @abstractmethod
    def open_application(
        self, app_id: str, *, confirmed: bool = False
    ) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def close_application(
        self, app_id: str, *, confirmed: bool = False
    ) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def capture_microscope(self) -> HubCaptureResult:
        raise NotImplementedError

    @abstractmethod
    def capture_thermal_camera(self) -> HubCaptureResult:
        raise NotImplementedError

    @abstractmethod
    def read_multimeter(self) -> HubReadingResult:
        raise NotImplementedError

    @abstractmethod
    def read_power_supply(self) -> HubReadingResult:
        raise NotImplementedError


class MockAlpilabHub(AlpilabHub):
    """In-memory Hub mock. Does NOT launch Windows programs or hardware."""

    name = "alpilab_hub_mock"

    def __init__(self, granted_permissions: set[str] | None = None) -> None:
        # None → permissive mock default; empty set → explicitly no grants.
        self._granted: set[str] = (
            {"*"} if granted_permissions is None else granted_permissions
        )

    def is_available(self) -> bool:
        return True

    def get_pc_status(self) -> HubPCStatus:
        return HubPCStatus(
            online=True,
            hostname="mock-lab-pc",
            os_name="Windows (mock)",
            hub_version="0.0.0-mock",
            capabilities=[
                "open_application",
                "close_application",
                "capture_microscope",
                "capture_thermal_camera",
                "read_multimeter",
                "read_power_supply",
                "get_pc_status",
            ],
        )

    def open_application(
        self, app_id: str, *, confirmed: bool = False
    ) -> HubActionResult:
        decision = evaluate_action(
            "open_application",
            confirmed=confirmed,
            granted_permissions=self._granted,
        )
        if not decision.allowed:
            return HubActionResult(
                success=False,
                action="open_application",
                message=decision.reason,
                requires_confirmation=decision.requires_confirmation,
                metadata={"app_id": app_id},
            )
        return HubActionResult(
            success=True,
            action="open_application",
            message=(
                f"[MOCK] Would open application '{app_id}'. "
                "No real process was started."
            ),
            metadata={"app_id": app_id},
        )

    def close_application(
        self, app_id: str, *, confirmed: bool = False
    ) -> HubActionResult:
        decision = evaluate_action(
            "close_application",
            confirmed=confirmed,
            granted_permissions=self._granted,
        )
        if not decision.allowed:
            return HubActionResult(
                success=False,
                action="close_application",
                message=decision.reason,
                requires_confirmation=decision.requires_confirmation,
                metadata={"app_id": app_id},
            )
        return HubActionResult(
            success=True,
            action="close_application",
            message=(
                f"[MOCK] Would close application '{app_id}'. "
                "No real process was terminated."
            ),
            metadata={"app_id": app_id},
        )

    def capture_microscope(self) -> HubCaptureResult:
        return HubCaptureResult(
            success=True,
            source="microscope",
            message="[MOCK] Microscope capture simulated. No hardware accessed.",
            storage_path=None,
        )

    def capture_thermal_camera(self) -> HubCaptureResult:
        return HubCaptureResult(
            success=True,
            source="thermal_camera",
            message="[MOCK] Thermal capture simulated. No hardware accessed.",
            storage_path=None,
        )

    def read_multimeter(self) -> HubReadingResult:
        return HubReadingResult(
            success=True,
            instrument="multimeter",
            value=0.0,
            unit="V",
            message="[MOCK] Multimeter reading simulated.",
        )

    def read_power_supply(self) -> HubReadingResult:
        return HubReadingResult(
            success=True,
            instrument="power_supply",
            value=0.0,
            unit="A",
            message="[MOCK] Power supply reading simulated.",
        )
