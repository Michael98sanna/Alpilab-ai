"""Future bridge toward Alpilab Check.

Alpilab Check is a separate Windows desktop application. Alpilab AI must NOT
import its internal modules. Communication will happen later via a stable
contract (HTTP/local bridge/file exchange/API) defined here.

This module only defines the interface and a clearly marked mock.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models import Device, DiagnosticTest, RepairSession


class AlpilabCheckConnector(ABC):
    """Abstract connector for exchanging repair/diagnostic data with Alpilab Check."""

    name: str = "alpilab_check"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when the bridge/endpoint is reachable."""
        raise NotImplementedError

    @abstractmethod
    def get_device(self, external_id: str) -> Device | None:
        """Fetch a device previously identified in Alpilab Check."""
        raise NotImplementedError

    @abstractmethod
    def list_diagnostic_tests(self, external_job_id: str) -> list[DiagnosticTest]:
        """List diagnostic tests associated with a Check job/session."""
        raise NotImplementedError

    @abstractmethod
    def import_repair_session(self, external_job_id: str) -> RepairSession | None:
        """Import a repair session snapshot into Alpilab AI domain models."""
        raise NotImplementedError

    @abstractmethod
    def export_notes(self, external_job_id: str, notes: list[str]) -> bool:
        """Push notes back toward Check (future). Returns success flag."""
        raise NotImplementedError

    def ping(self) -> dict[str, Any]:
        """Lightweight health probe for the bridge."""
        return {"connector": self.name, "available": self.is_available()}


class MockAlpilabCheckConnector(AlpilabCheckConnector):
    """In-memory stub. Does not talk to Alpilab Check or any network service."""

    name = "alpilab_check_mock"

    def __init__(self) -> None:
        self._devices: dict[str, Device] = {}
        self._tests: dict[str, list[DiagnosticTest]] = {}
        self._sessions: dict[str, RepairSession] = {}

    def is_available(self) -> bool:
        return True

    def register_device(self, external_id: str, device: Device) -> None:
        """Test helper: seed a device into the mock store."""
        self._devices[external_id] = device

    def register_tests(self, external_job_id: str, tests: list[DiagnosticTest]) -> None:
        self._tests[external_job_id] = list(tests)

    def register_session(self, external_job_id: str, session: RepairSession) -> None:
        self._sessions[external_job_id] = session

    def get_device(self, external_id: str) -> Device | None:
        return self._devices.get(external_id)

    def list_diagnostic_tests(self, external_job_id: str) -> list[DiagnosticTest]:
        return list(self._tests.get(external_job_id, []))

    def import_repair_session(self, external_job_id: str) -> RepairSession | None:
        return self._sessions.get(external_job_id)

    def export_notes(self, external_job_id: str, notes: list[str]) -> bool:
        # Mock accepts any job id; real bridge will validate.
        _ = external_job_id, notes
        return True
