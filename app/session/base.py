"""Session persistence contract — InMemory and SQLite implementations."""

from __future__ import annotations

from typing import Protocol

from app.schemas.session import (
    ClientDevice,
    RepairSessionContext,
    SessionParticipant,
    User,
)
from app.schemas.session_events import SessionEvent


class SessionStore(Protocol):
    def save_user(self, user: User) -> User: ...

    def save_client_device(self, device: ClientDevice) -> ClientDevice: ...

    def save_context(self, context: RepairSessionContext) -> RepairSessionContext: ...

    def get_context(self, repair_session_id: str) -> RepairSessionContext | None: ...

    def add_participant(self, participant: SessionParticipant) -> SessionParticipant: ...

    def participants_for_session(self, repair_session_id: str) -> list[SessionParticipant]: ...

    def client_devices_for_user(self, user_id: str) -> list[ClientDevice]: ...

    def active_contexts_for_user(self, user_id: str) -> list[RepairSessionContext]: ...

    def append_event(self, event: SessionEvent) -> SessionEvent: ...

    def recent_contexts(self, limit: int = 10) -> list[RepairSessionContext]: ...
