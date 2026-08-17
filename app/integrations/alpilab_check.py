"""Bridge toward Alpilab Check.

Alpilab Check is a separate Windows application. This module must never import
its internal code. A future implementation may talk to it through HTTP, a local
file drop, or Alpilab Hub.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import uuid4

from app.models import (
    Device,
    DeviceIdentifierType,
    DiagnosticTest,
    RepairSession,
    RepairSessionStatus,
    SourceSystem,
    DiagnosticStatus,
)


class AlpilabCheckConnector(ABC):
    """Stable integration surface for a future Check bridge."""

    name: str = "alpilab_check"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when a live Check endpoint/file/bridge is reachable."""

    @abstractmethod
    def fetch_device(self, identifier: str) -> Device | None:
        """Resolve a device by IMEI/serial if Check can provide it."""

    @abstractmethod
    def fetch_session_snapshot(self, session_id: str) -> RepairSession | None:
        """Return a repair snapshot exported by Check, mapped to shared models."""

    @abstractmethod
    def fetch_diagnostic_tests(self, session_id: str) -> list[DiagnosticTest]:
        """Return diagnostic tests associated with a Check session."""


class MockAlpilabCheckConnector(AlpilabCheckConnector):
    """In-memory stand-in. Does not contact Alpilab Check."""

    name = "mock_alpilab_check"

    def __init__(self) -> None:
        device = Device(
            brand="Apple",
            model="iPhone 12",
            identifier="000000000000000",
            identifier_type=DeviceIdentifierType.IMEI,
            os_name="iOS",
            notes="[MOCK] Sample device. Not read from Alpilab Check.",
        )
        test = DiagnosticTest(
            name="Battery health",
            category="battery",
            status=DiagnosticStatus.UNKNOWN,
            details="[MOCK] No real diagnostic was executed.",
            source=SourceSystem.ALPILAB_CHECK,
        )
        self._device = device
        self._session = RepairSession(
            device=device,
            status=RepairSessionStatus.OPEN,
            technician="mock",
            source=SourceSystem.ALPILAB_CHECK,
            diagnostic_tests=[test],
        )
        self._session_id = str(self._session.id)

    def is_available(self) -> bool:
        return True

    def fetch_device(self, identifier: str) -> Device | None:
        if identifier == self._device.identifier:
            return self._device.model_copy()
        return None

    def fetch_session_snapshot(self, session_id: str) -> RepairSession | None:
        if session_id in {self._session_id, "mock"}:
            return self._session.model_copy(deep=True)
        return None

    def fetch_diagnostic_tests(self, session_id: str) -> list[DiagnosticTest]:
        snapshot = self.fetch_session_snapshot(session_id)
        if snapshot is None:
            return []
        return list(snapshot.diagnostic_tests)

    @property
    def sample_session_id(self) -> str:
        return self._session_id

    def unused_uuid(self) -> str:
        return str(uuid4())
