"""Alpilab Hub client interface and Mock implementation.

Future capabilities (declared, not executed):
- open_application / close_application
- capture_microscope / capture_thermal_camera
- read_multimeter / read_power_supply
- get_pc_status
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.security import require_confirmation
from hub.schemas import HubActionResult, PCStatus


class AlpilabHub(ABC):
    """Contract for the future Windows Hub service."""

    name: str = "alpilab_hub"

    @abstractmethod
    def get_pc_status(self) -> PCStatus:
        ...

    @abstractmethod
    def open_application(self, app_id: str, *, confirmed: bool = False) -> HubActionResult:
        ...

    @abstractmethod
    def close_application(self, app_id: str, *, confirmed: bool = False) -> HubActionResult:
        ...

    @abstractmethod
    def capture_microscope(self, *, confirmed: bool = False) -> HubActionResult:
        ...

    @abstractmethod
    def capture_thermal_camera(self, *, confirmed: bool = False) -> HubActionResult:
        ...

    @abstractmethod
    def read_multimeter(self, *, confirmed: bool = False) -> HubActionResult:
        ...

    @abstractmethod
    def read_power_supply(self, *, confirmed: bool = False) -> HubActionResult:
        ...


class MockAlpilabHub(AlpilabHub):
    """MOCK Hub — returns stub results and never touches the OS.

    Application open/close are treated as potentially dangerous and require
    ``confirmed=True``. Capture/read mocks also require confirmation to exercise
    the security gate early.
    """

    name = "alpilab_hub_mock"

    _CAPABILITIES = [
        "open_application",
        "close_application",
        "capture_microscope",
        "capture_thermal_camera",
        "read_multimeter",
        "read_power_supply",
        "get_pc_status",
    ]

    def get_pc_status(self) -> PCStatus:
        return PCStatus(
            online=True,
            hostname="mock-lab-pc",
            os="Windows (mock)",
            hub_version="0.0.0-mock",
            capabilities=list(self._CAPABILITIES),
        )

    def open_application(self, app_id: str, *, confirmed: bool = False) -> HubActionResult:
        require_confirmation(confirmed, f"open_application:{app_id}")
        return HubActionResult(
            success=True,
            action="open_application",
            message=f"[MOCK] open_application richiesto per '{app_id}' — nessuna app avviata.",
            mock=True,
            data={"app_id": app_id},
            requires_confirmation=True,
        )

    def close_application(self, app_id: str, *, confirmed: bool = False) -> HubActionResult:
        require_confirmation(confirmed, f"close_application:{app_id}")
        return HubActionResult(
            success=True,
            action="close_application",
            message=f"[MOCK] close_application richiesto per '{app_id}' — nessuna app chiusa.",
            mock=True,
            data={"app_id": app_id},
            requires_confirmation=True,
        )

    def capture_microscope(self, *, confirmed: bool = False) -> HubActionResult:
        require_confirmation(confirmed, "capture_microscope")
        return HubActionResult(
            success=True,
            action="capture_microscope",
            message="[MOCK] Cattura microscopio simulata — nessun hardware interrogato.",
            mock=True,
            data={"image_path": None},
            requires_confirmation=True,
        )

    def capture_thermal_camera(self, *, confirmed: bool = False) -> HubActionResult:
        require_confirmation(confirmed, "capture_thermal_camera")
        return HubActionResult(
            success=True,
            action="capture_thermal_camera",
            message="[MOCK] Cattura termocamera simulata — nessun hardware interrogato.",
            mock=True,
            data={"image_path": None},
            requires_confirmation=True,
        )

    def read_multimeter(self, *, confirmed: bool = False) -> HubActionResult:
        require_confirmation(confirmed, "read_multimeter")
        return HubActionResult(
            success=True,
            action="read_multimeter",
            message="[MOCK] Lettura multimetro simulata.",
            mock=True,
            data={"value": None, "unit": None},
            requires_confirmation=True,
        )

    def read_power_supply(self, *, confirmed: bool = False) -> HubActionResult:
        require_confirmation(confirmed, "read_power_supply")
        return HubActionResult(
            success=True,
            action="read_power_supply",
            message="[MOCK] Lettura alimentatore simulata.",
            mock=True,
            data={"voltage": None, "current": None},
            requires_confirmation=True,
        )
