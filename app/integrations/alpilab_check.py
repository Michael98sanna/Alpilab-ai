"""Future bridge toward Alpilab Check.

Alpilab Check is a separate Windows desktop application. This connector is an
abstraction only: no Check source code is imported, and no assumption is made
about its internal implementation.

Future transport options (not implemented here):
- local HTTP API
- file exchange
- named pipe / local socket bridge
- Hub-mediated relay
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.schemas import Device, DiagnosticTest, Measurement


@dataclass
class CheckDeviceSnapshot:
    """Normalized device info as received from Check (future)."""

    device: Device
    source: str = "alpilab_check"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckDiagnosticsSnapshot:
    """Normalized diagnostics payload from Check (future)."""

    tests: list[DiagnosticTest] = field(default_factory=list)
    measurements: list[Measurement] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


class AlpilabCheckConnector(ABC):
    """Contract for exchanging data with Alpilab Check without code coupling."""

    name: str = "alpilab_check"

    @abstractmethod
    def is_available(self) -> bool:
        """True when a Check bridge endpoint is reachable."""
        raise NotImplementedError

    @abstractmethod
    def get_connected_device(self) -> CheckDeviceSnapshot | None:
        """Return the device currently identified in Check, if any."""
        raise NotImplementedError

    @abstractmethod
    def get_diagnostics(self) -> CheckDiagnosticsSnapshot | None:
        """Return the latest diagnostics snapshot exported by Check."""
        raise NotImplementedError

    @abstractmethod
    def push_session_reference(self, session_id: str) -> bool:
        """Share an Alpilab AI session id back to Check (future)."""
        raise NotImplementedError


class MockAlpilabCheckConnector(AlpilabCheckConnector):
    """MOCK connector for tests and local development. No real Check access."""

    name = "alpilab_check_mock"

    def __init__(self, *, available: bool = True) -> None:
        self._available = available
        self._pushed_sessions: list[str] = []

    def is_available(self) -> bool:
        return self._available

    def get_connected_device(self) -> CheckDeviceSnapshot | None:
        if not self._available:
            return None
        return CheckDeviceSnapshot(
            device=Device(
                brand="Apple",
                model="iPhone 12",
                model_code="A2403",
                notes="MOCK device from AlpilabCheckConnector",
            ),
            source=self.name,
            raw={"mock": True},
        )

    def get_diagnostics(self) -> CheckDiagnosticsSnapshot | None:
        if not self._available:
            return None
        return CheckDiagnosticsSnapshot(
            tests=[
                DiagnosticTest(
                    name="battery_health",
                    category="power",
                    result="87%",
                    passed=True,
                )
            ],
            measurements=[
                Measurement(
                    source="check_export",
                    label="battery_cycle_count",
                    value=412,
                    unit="cycles",
                )
            ],
            raw={"mock": True},
        )

    def push_session_reference(self, session_id: str) -> bool:
        if not self._available:
            return False
        self._pushed_sessions.append(session_id)
        return True
