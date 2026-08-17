"""
Alpilab Check bridge — abstraction only.

Alpilab Check is a separate Windows desktop application used at the bench.
Alpilab AI must NOT import its internal modules.

Future communication will happen via a stable contract such as:
- local HTTP bridge
- shared exchange files
- documented API

This module defines the interface and a clearly labeled mock.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class CheckDeviceSnapshot(BaseModel):
    """Normalized device info as received from Alpilab Check (contract sketch)."""

    brand: str | None = None
    model: str | None = None
    imei: str | None = None
    serial_number: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class CheckDiagnosticPayload(BaseModel):
    """Normalized diagnostic payload from Alpilab Check (contract sketch)."""

    test_name: str
    status: str
    details: dict[str, Any] = Field(default_factory=dict)


class AlpilabCheckConnector(ABC):
    """
    Future connector interface toward Alpilab Check.

    Implementations must treat Check as an external system.
    """

    name: str = "alpilab_check"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when a bridge/session to Check is reachable."""
        raise NotImplementedError

    @abstractmethod
    def get_connected_device(self) -> CheckDeviceSnapshot | None:
        """Fetch the currently identified device from Check, if any."""
        raise NotImplementedError

    @abstractmethod
    def get_latest_diagnostics(self) -> list[CheckDiagnosticPayload]:
        """Fetch recent diagnostic results exposed by Check."""
        raise NotImplementedError

    @abstractmethod
    def ping(self) -> bool:
        """Lightweight health check of the bridge."""
        raise NotImplementedError


class MockAlpilabCheckConnector(AlpilabCheckConnector):
    """
    Mock connector for tests and local development.

    Does not contact Alpilab Check. Clearly identified as mock.
    """

    name = "alpilab_check_mock"

    def __init__(self, available: bool = True) -> None:
        self._available = available

    def is_available(self) -> bool:
        return self._available

    def get_connected_device(self) -> CheckDeviceSnapshot | None:
        if not self._available:
            return None
        return CheckDeviceSnapshot(
            brand="apple",
            model="iPhone 13",
            imei="000000000000000",
            serial_number="MOCKSERIAL",
            raw={"source": "mock", "note": "Dati fittizi — non provenienti da Check"},
        )

    def get_latest_diagnostics(self) -> list[CheckDiagnosticPayload]:
        if not self._available:
            return []
        return [
            CheckDiagnosticPayload(
                test_name="battery_health",
                status="passed",
                details={"mock": True, "health_percent": 87},
            )
        ]

    def ping(self) -> bool:
        return self._available
