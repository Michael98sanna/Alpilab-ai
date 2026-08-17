"""In-memory session persistence (development / tests)."""

from datetime import datetime, timezone

from app.schemas.session import (
    ClientDevice,
    RepairSessionContext,
    SessionParticipant,
    User,
)
from app.schemas.session_events import SessionEvent


class InMemorySessionStore:
    """Mock persistence layer without cloud database."""

    def __init__(self) -> None:
        self.users: dict[str, User] = {}
        self.client_devices: dict[str, ClientDevice] = {}
        self.contexts: dict[str, RepairSessionContext] = {}
        self.participants: dict[str, SessionParticipant] = {}
        self.event_log: list[SessionEvent] = []

    def save_user(self, user: User) -> User:
        self.users[user.id] = user
        return user

    def save_client_device(self, device: ClientDevice) -> ClientDevice:
        self.client_devices[device.id] = device
        return device

    def save_context(self, context: RepairSessionContext) -> RepairSessionContext:
        context.last_activity_at = datetime.now(timezone.utc)
        self.contexts[context.repair_session_id] = context
        return context

    def get_context(self, repair_session_id: str) -> RepairSessionContext | None:
        return self.contexts.get(repair_session_id)

    def add_participant(self, participant: SessionParticipant) -> SessionParticipant:
        self.participants[participant.id] = participant
        context = self.contexts.get(participant.repair_session_id)
        if context is not None:
            if participant.id not in context.active_participant_ids:
                context.active_participant_ids.append(participant.id)
            context.last_active_client_device_id = participant.client_device_id
            self.save_context(context)
        return participant

    def participants_for_session(self, repair_session_id: str) -> list[SessionParticipant]:
        return [
            p
            for p in self.participants.values()
            if p.repair_session_id == repair_session_id and p.is_active
        ]

    def client_devices_for_user(self, user_id: str) -> list[ClientDevice]:
        return [d for d in self.client_devices.values() if d.user_id == user_id]

    def active_contexts_for_user(self, user_id: str) -> list[RepairSessionContext]:
        user_device_ids = {d.id for d in self.client_devices_for_user(user_id)}
        session_ids = {
            p.repair_session_id
            for p in self.participants.values()
            if p.client_device_id in user_device_ids and p.is_active
        }
        return [self.contexts[sid] for sid in session_ids if sid in self.contexts]

    def append_event(self, event: SessionEvent) -> SessionEvent:
        self.event_log.append(event)
        return event

    def recent_contexts(self, limit: int = 10) -> list[RepairSessionContext]:
        items = sorted(
            self.contexts.values(),
            key=lambda c: c.last_activity_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return items[:limit]
