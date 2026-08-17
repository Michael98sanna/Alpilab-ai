"""Alpilab Check bridge — interface only.

Alpilab Check is a separate Windows application. This module defines the
future integration contract. It does NOT import Check internals and does NOT
assume how Check works internally.

Future transport options (not implemented): HTTP API, local bridge, file export.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CheckDeviceSnapshot:
    """Normalized device info that Check might expose in the future."""

    brand: str | None = None
    model: str | None = None
    imei: str | None = None
    serial_number: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckDiagnosticSnapshot:
    """Normalized diagnostic payload from Check (future)."""

    summary: str | None = None
    tests: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


class AlpilabCheckConnector(ABC):
    """Abstract connector for future Alpilab Check integration."""

    name: str = "alpilab_check"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when a Check endpoint/bridge is reachable."""
        raise NotImplementedError

    @abstractmethod
    def get_device_snapshot(self) -> CheckDeviceSnapshot | None:
        """Fetch the currently selected device from Check, if any."""
        raise NotImplementedError

    @abstractmethod
    def get_diagnostic_snapshot(self) -> CheckDiagnosticSnapshot | None:
        """Fetch the latest diagnostic results from Check, if any."""
        raise NotImplementedError

    @abstractmethod
    def ping(self) -> bool:
        """Lightweight connectivity check."""
        raise NotImplementedError


class MockAlpilabCheckConnector(AlpilabCheckConnector):
    """MOCK connector — clearly fake data for architecture tests only."""

    name = "alpilab_check_mock"

    def __init__(
        self,
        *,
        available: bool = True,
        device: CheckDeviceSnapshot | None = None,
        diagnostic: CheckDiagnosticSnapshot | None = None,
    ) -> None:
        self._available = available
        self._device = device or CheckDeviceSnapshot(
            brand="Apple",
            model="iPhone 12",
            imei="000000000000000",
            raw={"mock": True},
        )
        self._diagnostic = diagnostic or CheckDiagnosticSnapshot(
            summary="[MOCK] Nessuna diagnosi reale — connettore di test.",
            tests=[{"name": "battery_health", "status": "unknown", "mock": True}],
            raw={"mock": True},
        )

    def is_available(self) -> bool:
        return self._available

    def get_device_snapshot(self) -> CheckDeviceSnapshot | None:
        if not self._available:
            return None
        return self._device

    def get_diagnostic_snapshot(self) -> CheckDiagnosticSnapshot | None:
        if not self._available:
            return None
        return self._diagnostic

    def ping(self) -> bool:
        return self._available
