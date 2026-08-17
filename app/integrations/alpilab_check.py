"""Future bridge to Alpilab Check.

IMPORTANT:
- This is an abstraction only.
- Do NOT import Alpilab Check source code.
- Do NOT assume Check internals.
- Integration will happen later via a stable API / file / HTTP / local bridge.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class CheckDeviceSnapshot(BaseModel):
    """Normalized device data as received from Alpilab Check (future)."""

    external_id: str | None = None
    brand: str | None = None
    model: str | None = None
    model_code: str | None = None
    imei: str | None = None
    serial_number: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class CheckDiagnosticPayload(BaseModel):
    """Normalized diagnostic payload from Alpilab Check (future)."""

    external_session_id: str | None = None
    tests: list[dict[str, Any]] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class AlpilabCheckConnector(ABC):
    """Contract for exchanging data with Alpilab Check.

    Implementations may use HTTP, local IPC, shared files, or a Hub proxy.
    None of that is implemented in phase 1.
    """

    name: str = "alpilab_check"

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def fetch_device(self, external_id: str) -> CheckDeviceSnapshot | None:
        raise NotImplementedError

    @abstractmethod
    def fetch_diagnostics(
        self, external_session_id: str
    ) -> CheckDiagnosticPayload | None:
        raise NotImplementedError

    @abstractmethod
    def push_repair_summary(
        self, external_session_id: str, summary: dict[str, Any]
    ) -> bool:
        """Push a repair summary back to Check when supported."""
        raise NotImplementedError


class MockAlpilabCheckConnector(AlpilabCheckConnector):
    """In-memory mock. Clearly identified — not a real Check integration."""

    name = "alpilab_check_mock"

    def __init__(self) -> None:
        self._devices: dict[str, CheckDeviceSnapshot] = {
            "demo-1": CheckDeviceSnapshot(
                external_id="demo-1",
                brand="apple",
                model="iPhone 12",
                model_code="A2403",
                imei="356938035643809",
                raw={"source": "mock"},
            )
        }
        self._diagnostics: dict[str, CheckDiagnosticPayload] = {
            "session-demo": CheckDiagnosticPayload(
                external_session_id="session-demo",
                tests=[
                    {"name": "battery_health", "result": "87%", "passed": True},
                    {"name": "touch", "result": "ok", "passed": True},
                ],
                raw={"source": "mock"},
            )
        }

    def is_available(self) -> bool:
        return True

    def fetch_device(self, external_id: str) -> CheckDeviceSnapshot | None:
        return self._devices.get(external_id)

    def fetch_diagnostics(
        self, external_session_id: str
    ) -> CheckDiagnosticPayload | None:
        return self._diagnostics.get(external_session_id)

    def push_repair_summary(
        self, external_session_id: str, summary: dict[str, Any]
    ) -> bool:
        # Mock accepts any summary and reports success without side effects.
        _ = (external_session_id, summary)
        return True
