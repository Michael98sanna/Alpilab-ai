"""In-memory Hub mock.

Returns structured placeholders. Does not start processes, touch hardware,
or interpret strings as shell commands.
"""

from __future__ import annotations

from app.core.security import (
    DANGEROUS_CAPABILITIES,
    PermissionContext,
    require_explicit_confirmation,
    require_permission,
)

from .interface import AlpilabHub
from .schemas import (
    HUB_CAPABILITIES,
    ApplicationActionRequest,
    HubResult,
    PcStatus,
)

_KNOWN_APPLICATIONS = frozenset(
    {
        "3utools",
        "borneo",
        "zxw",
        "alpilab_check",
    }
)


class MockAlpilabHub(AlpilabHub):
    """Always-available fake Hub used in tests and local development."""

    def get_pc_status(self, permissions: PermissionContext) -> PcStatus:
        require_permission(permissions, "get_pc_status")
        return PcStatus(
            reachable=True,
            hostname="mock-bench-pc",
            is_mock=True,
            capabilities=list(HUB_CAPABILITIES),
            notes="Mock Hub: nessun PC reale è collegato.",
        )

    def open_application(
        self,
        request: ApplicationActionRequest,
        permissions: PermissionContext,
    ) -> HubResult:
        return self._application_action("open_application", request, permissions)

    def close_application(
        self,
        request: ApplicationActionRequest,
        permissions: PermissionContext,
    ) -> HubResult:
        return self._application_action("close_application", request, permissions)

    def capture_microscope(self, permissions: PermissionContext) -> HubResult:
        require_permission(permissions, "capture_microscope")
        return self._not_executed(
            "capture_microscope",
            "Mock: nessuna cattura microscopio. Hardware non collegato.",
        )

    def capture_thermal_camera(self, permissions: PermissionContext) -> HubResult:
        require_permission(permissions, "capture_thermal_camera")
        return self._not_executed(
            "capture_thermal_camera",
            "Mock: nessuna cattura termocamera. Hardware non collegato.",
        )

    def read_multimeter(self, permissions: PermissionContext) -> HubResult:
        require_permission(permissions, "read_multimeter")
        return self._not_executed(
            "read_multimeter",
            "Mock: nessuna lettura multimetro. Hardware non collegato.",
        )

    def read_power_supply(self, permissions: PermissionContext) -> HubResult:
        require_permission(permissions, "read_power_supply")
        return self._not_executed(
            "read_power_supply",
            "Mock: nessuna lettura alimentatore. Hardware non collegato.",
        )

    def _application_action(
        self,
        capability: str,
        request: ApplicationActionRequest,
        permissions: PermissionContext,
    ) -> HubResult:
        require_permission(permissions, capability)
        if capability in DANGEROUS_CAPABILITIES:
            require_explicit_confirmation(request.confirmed, capability)

        logical_name = request.application.strip().lower()
        if logical_name not in _KNOWN_APPLICATIONS:
            return HubResult(
                capability=capability,
                ok=False,
                executed=False,
                is_mock=True,
                message=(
                    f"Applicazione '{request.application}' non è nella allow-list. "
                    "Nessun comando è stato eseguito."
                ),
                data={"application": request.application},
            )

        return HubResult(
            capability=capability,
            ok=True,
            executed=False,
            is_mock=True,
            message=(
                f"Mock: azione '{capability}' su '{logical_name}' accettata "
                "ma NON eseguita. Nessun processo Windows è stato avviato."
            ),
            data={"application": logical_name},
        )

    @staticmethod
    def _not_executed(capability: str, message: str) -> HubResult:
        return HubResult(
            capability=capability,
            ok=True,
            executed=False,
            is_mock=True,
            message=message,
        )
