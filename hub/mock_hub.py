"""Mock Alpilab Hub for development and tests."""

from hub.alpilab_hub import (
    AlpilabHub,
    HubActionResult,
    HubCapability,
    PCStatus,
)


class MockAlpilabHub(AlpilabHub):
    """Placeholder Hub that simulates local hardware/software actions."""

    def __init__(self, available: bool = True) -> None:
        self._available = available
        self._open_apps: set[str] = set()

    def is_available(self) -> bool:
        return self._available

    def capabilities(self) -> set[HubCapability]:
        return set(HubCapability)

    def open_application(self, application_name: str) -> HubActionResult:
        if not self._available:
            return HubActionResult(success=False, message="Hub non disponibile")
        self._open_apps.add(application_name)
        return HubActionResult(
            success=True,
            message=f"[MOCK] Applicazione aperta: {application_name}",
            data={"application": application_name},
            requires_confirmation=True,
        )

    def close_application(self, application_name: str) -> HubActionResult:
        if not self._available:
            return HubActionResult(success=False, message="Hub non disponibile")
        self._open_apps.discard(application_name)
        return HubActionResult(
            success=True,
            message=f"[MOCK] Applicazione chiusa: {application_name}",
            data={"application": application_name},
        )

    def capture_microscope(self) -> HubActionResult:
        return self._mock_capture("microscope")

    def capture_thermal_camera(self) -> HubActionResult:
        return self._mock_capture("thermal_camera")

    def read_multimeter(self) -> HubActionResult:
        return HubActionResult(
            success=self._available,
            message="[MOCK] Lettura multimetro",
            data={"value": 3.82, "unit": "V", "label": "voltage"},
        )

    def read_power_supply(self) -> HubActionResult:
        return HubActionResult(
            success=self._available,
            message="[MOCK] Lettura alimentatore",
            data={"voltage": 4.2, "current": 0.5, "output_enabled": True},
        )

    def get_pc_status(self) -> PCStatus:
        return PCStatus(
            online=self._available,
            hostname="mock-pc",
            connected_devices=["multimeter", "microscope"],
            metadata={"mock": True},
        )

    def _mock_capture(self, device: str) -> HubActionResult:
        if not self._available:
            return HubActionResult(success=False, message="Hub non disponibile")
        return HubActionResult(
            success=True,
            message=f"[MOCK] Immagine acquisita da {device}",
            data={"device": device, "storage_reference": f"mock/{device}.jpg"},
            requires_confirmation=True,
        )
