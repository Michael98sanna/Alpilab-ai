"""In-memory repair session service (no database in this phase)."""

from __future__ import annotations

from app.models.repair import (
    CustomerIssue,
    Device,
    DiagnosticTest,
    Measurement,
    Note,
    RepairSession,
    SessionStatus,
)


class RepairService:
    """CRUD-like helpers over an in-memory store. Replace with DB later."""

    def __init__(self) -> None:
        self._sessions: dict[str, RepairSession] = {}

    def create_session(
        self,
        device: Device,
        issue: CustomerIssue,
        *,
        technician: str | None = None,
    ) -> RepairSession:
        session = RepairSession(
            device=device,
            issue=issue,
            technician=technician,
            status=SessionStatus.OPEN,
        )
        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> RepairSession | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[RepairSession]:
        return list(self._sessions.values())

    def add_test(self, session_id: str, test: DiagnosticTest) -> RepairSession:
        session = self._require(session_id)
        session.add_test(test)
        session.status = SessionStatus.IN_PROGRESS
        return session

    def add_measurement(
        self, session_id: str, measurement: Measurement
    ) -> RepairSession:
        session = self._require(session_id)
        session.add_measurement(measurement)
        return session

    def add_note(self, session_id: str, note: Note) -> RepairSession:
        session = self._require(session_id)
        session.add_note(note)
        return session

    def _require(self, session_id: str) -> RepairSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"RepairSession not found: {session_id}")
        return session
