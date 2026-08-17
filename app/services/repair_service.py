"""In-memory repair session service — foundation stub, not a database.

MOCK STORAGE: data lives only in process memory and is lost on restart.
"""

from __future__ import annotations

from app.models.device import Device
from app.models.repair import RepairSession, SessionStatus


class RepairService:
    """Minimal CRUD-like helpers for early API / tests.

    Replace with a real repository + PostgreSQL/SQLite later.
    """

    def __init__(self) -> None:
        self._devices: dict[str, Device] = {}
        self._sessions: dict[str, RepairSession] = {}

    def create_device(self, device: Device) -> Device:
        self._devices[device.id] = device
        return device

    def get_device(self, device_id: str) -> Device | None:
        return self._devices.get(device_id)

    def open_session(self, device_id: str, *, technician: str | None = None) -> RepairSession:
        if device_id not in self._devices:
            raise KeyError(f"Device non trovato: {device_id}")
        session = RepairSession(
            device_id=device_id,
            status=SessionStatus.INTAKE,
            technician=technician,
        )
        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> RepairSession | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[RepairSession]:
        return list(self._sessions.values())
