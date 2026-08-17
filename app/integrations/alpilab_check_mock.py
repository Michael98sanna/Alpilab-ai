"""Mock Alpilab Check connector for development and tests."""

from typing import Any

from .alpilab_check import (
    AlpilabCheckConnector,
    CheckDeviceInfo,
    CheckDiagnosticSnapshot,
)


class MockAlpilabCheckConnector(AlpilabCheckConnector):
    """Placeholder connector that simulates Alpilab Check responses."""

    def __init__(self, connected: bool = True) -> None:
        self._connected = connected

    def is_connected(self) -> bool:
        return self._connected

    def get_device_info(self, device_reference: str) -> CheckDeviceInfo | None:
        if not self._connected:
            return None
        return CheckDeviceInfo(
            brand="MockBrand",
            model="MockModel",
            variant="128GB",
            serial_number=device_reference,
            raw={"source": "mock_alpilab_check"},
        )

    def get_diagnostic_snapshot(
        self, session_reference: str
    ) -> CheckDiagnosticSnapshot | None:
        if not self._connected:
            return None
        return CheckDiagnosticSnapshot(
            session_reference=session_reference,
            tests=[{"name": "battery_health", "result": "82%"}],
            measurements=[{"label": "voltage", "value": 3.8, "unit": "V"}],
            captured_at="2026-01-01T00:00:00Z",
            raw={"source": "mock_alpilab_check"},
        )

    def push_repair_update(self, payload: dict[str, Any]) -> bool:
        return self._connected and bool(payload)
