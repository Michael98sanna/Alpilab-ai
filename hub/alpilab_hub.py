"""
Alpilab Hub — conceptual Windows bridge (interfaces + mock only).

Hub will eventually bridge cloud Alpilab AI to local PC software/hardware:
- applications (3uTools, Borneo, ZXW, …)
- instruments (microscope, thermal camera, multimeter, power supply)

SECURITY CONSTRAINTS (foundation and forever):
- NO arbitrary shell command execution
- NO remote shell
- NO real Windows process control in this phase
- Future dangerous actions require explicit confirmation + permissions

This package only defines interfaces and a mock implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class HubActionRisk(str, Enum):
    SAFE = "safe"
    ELEVATED = "elevated"
    DANGEROUS = "dangerous"


class HubPermission(str, Enum):
    OPEN_APPLICATION = "open_application"
    CLOSE_APPLICATION = "close_application"
    CAPTURE_MICROSCOPE = "capture_microscope"
    CAPTURE_THERMAL = "capture_thermal_camera"
    READ_MULTIMETER = "read_multimeter"
    READ_POWER_SUPPLY = "read_power_supply"
    GET_PC_STATUS = "get_pc_status"


class HubActionRequest(BaseModel):
    """Request for a Hub capability. Dangerous actions must be confirmed."""

    action: HubPermission
    params: dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False
    risk: HubActionRisk = HubActionRisk.SAFE


class HubActionResult(BaseModel):
    """Result of a Hub capability call."""

    success: bool
    action: HubPermission
    message: str
    is_mock: bool = True
    data: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False


class PcStatus(BaseModel):
    """High-level PC status reported by Hub."""

    online: bool
    hostname: str | None = None
    os_name: str | None = None
    applications: list[str] = Field(default_factory=list)
    instruments: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


# Actions that must never run without explicit confirmation (future enforcement).
DANGEROUS_ACTIONS: frozenset[HubPermission] = frozenset(
    {
        HubPermission.OPEN_APPLICATION,
        HubPermission.CLOSE_APPLICATION,
    }
)


class AlpilabHub(ABC):
    """Abstract Hub capability surface."""

    name: str = "alpilab_hub"

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_pc_status(self) -> PcStatus:
        raise NotImplementedError

    @abstractmethod
    def open_application(self, app_name: str, *, confirmed: bool = False) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def close_application(self, app_name: str, *, confirmed: bool = False) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def capture_microscope(self) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def capture_thermal_camera(self) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def read_multimeter(self) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def read_power_supply(self) -> HubActionResult:
        raise NotImplementedError


class MockAlpilabHub(AlpilabHub):
    """
    Mock Hub for architecture and tests.

    Does not launch Windows programs, does not run shell commands,
    and does not talk to real hardware.
    """

    name = "alpilab_hub_mock"

    def __init__(self, available: bool = True) -> None:
        self._available = available
        self._permissions: set[HubPermission] = set(HubPermission)

    def is_available(self) -> bool:
        return self._available

    def get_pc_status(self) -> PcStatus:
        return PcStatus(
            online=self._available,
            hostname="mock-lab-pc",
            os_name="Windows (mock)",
            applications=["3uTools (mock)", "Borneo (mock)"],
            instruments=["microscope (mock)", "multimeter (mock)"],
            metadata={"is_mock": True},
        )

    def _guard_dangerous(self, action: HubPermission, confirmed: bool) -> HubActionResult | None:
        if action in DANGEROUS_ACTIONS and not confirmed:
            return HubActionResult(
                success=False,
                action=action,
                message=(
                    "Azione potenzialmente pericolosa: conferma esplicita richiesta. "
                    "Nessun comando eseguito."
                ),
                is_mock=True,
                requires_confirmation=True,
            )
        return None

    def open_application(self, app_name: str, *, confirmed: bool = False) -> HubActionResult:
        blocked = self._guard_dangerous(HubPermission.OPEN_APPLICATION, confirmed)
        if blocked:
            return blocked
        return HubActionResult(
            success=True,
            action=HubPermission.OPEN_APPLICATION,
            message=f"[MOCK] open_application simulato per '{app_name}'. Nessun processo avviato.",
            data={"app_name": app_name},
        )

    def close_application(self, app_name: str, *, confirmed: bool = False) -> HubActionResult:
        blocked = self._guard_dangerous(HubPermission.CLOSE_APPLICATION, confirmed)
        if blocked:
            return blocked
        return HubActionResult(
            success=True,
            action=HubPermission.CLOSE_APPLICATION,
            message=f"[MOCK] close_application simulato per '{app_name}'. Nessun processo terminato.",
            data={"app_name": app_name},
        )

    def capture_microscope(self) -> HubActionResult:
        return HubActionResult(
            success=True,
            action=HubPermission.CAPTURE_MICROSCOPE,
            message="[MOCK] Cattura microscopio simulata. Nessuna periferica reale.",
            data={"image_path": None},
        )

    def capture_thermal_camera(self) -> HubActionResult:
        return HubActionResult(
            success=True,
            action=HubPermission.CAPTURE_THERMAL,
            message="[MOCK] Cattura termocamera simulata. Nessuna periferica reale.",
            data={"image_path": None},
        )

    def read_multimeter(self) -> HubActionResult:
        return HubActionResult(
            success=True,
            action=HubPermission.READ_MULTIMETER,
            message="[MOCK] Lettura multimetro simulata.",
            data={"value": 0.0, "unit": "V"},
        )

    def read_power_supply(self) -> HubActionResult:
        return HubActionResult(
            success=True,
            action=HubPermission.READ_POWER_SUPPLY,
            message="[MOCK] Lettura alimentatore simulata.",
            data={"voltage": 0.0, "current": 0.0},
        )
