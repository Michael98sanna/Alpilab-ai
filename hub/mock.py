"""Mock Alpilab Hub.

Returns structured placeholders. Does not start processes, open sockets to
lab software, or run shell commands.
"""

from __future__ import annotations

from app.core.security import PermissionContext, require_confirmation

from .base import AlpilabHub, HubResult, KnownApplication
from .permissions import (
    CAPTURE_MICROSCOPE,
    CAPTURE_THERMAL_CAMERA,
    CLOSE_APPLICATION,
    GET_PC_STATUS,
    OPEN_APPLICATION,
    READ_MULTIMETER,
    READ_POWER_SUPPLY,
)


class MockAlpilabHub(AlpilabHub):
    name = "mock_alpilab_hub"

    def is_available(self) -> bool:
        return True

    def get_pc_status(self, permission: PermissionContext) -> HubResult:
        permission.require(GET_PC_STATUS)
        return HubResult(
            ok=True,
            action=GET_PC_STATUS,
            is_mock=True,
            message="[MOCK HUB] PC status is not read from a real machine.",
            data={"online": False, "reason": "mock"},
        )

    def open_application(
        self,
        application: KnownApplication,
        permission: PermissionContext,
    ) -> HubResult:
        permission.require(OPEN_APPLICATION)
        return HubResult(
            ok=True,
            action=OPEN_APPLICATION,
            is_mock=True,
            message=f"[MOCK HUB] Would request to open '{application.value}'. No process started.",
            data={"application": application.value},
        )

    def close_application(
        self,
        application: KnownApplication,
        permission: PermissionContext,
        *,
        confirmed: bool = False,
    ) -> HubResult:
        permission.require(CLOSE_APPLICATION)
        require_confirmation(confirmed, CLOSE_APPLICATION)
        return HubResult(
            ok=True,
            action=CLOSE_APPLICATION,
            is_mock=True,
            message=(
                f"[MOCK HUB] Would request to close '{application.value}'. "
                "No process was stopped."
            ),
            data={"application": application.value, "confirmed": True},
        )

    def capture_microscope(self, permission: PermissionContext) -> HubResult:
        permission.require(CAPTURE_MICROSCOPE)
        return HubResult(
            ok=True,
            action=CAPTURE_MICROSCOPE,
            is_mock=True,
            message="[MOCK HUB] Microscope capture is not connected.",
            data={"image": None},
        )

    def capture_thermal_camera(self, permission: PermissionContext) -> HubResult:
        permission.require(CAPTURE_THERMAL_CAMERA)
        return HubResult(
            ok=True,
            action=CAPTURE_THERMAL_CAMERA,
            is_mock=True,
            message="[MOCK HUB] Thermal camera capture is not connected.",
            data={"image": None},
        )

    def read_multimeter(self, permission: PermissionContext) -> HubResult:
        permission.require(READ_MULTIMETER)
        return HubResult(
            ok=True,
            action=READ_MULTIMETER,
            is_mock=True,
            message="[MOCK HUB] Multimeter is not connected.",
            data={"value": None, "unit": None},
        )

    def read_power_supply(self, permission: PermissionContext) -> HubResult:
        permission.require(READ_POWER_SUPPLY)
        return HubResult(
            ok=True,
            action=READ_POWER_SUPPLY,
            is_mock=True,
            message="[MOCK HUB] Power supply is not connected.",
            data={"voltage": None, "current": None},
        )
