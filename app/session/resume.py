"""Automatic session resume across devices."""

from app.schemas.session import RepairSessionContext, SessionParticipant
from app.session.store import InMemorySessionStore


class SessionResumeManager:
    """
    Supports transparent device switching without creating a new repair session.

    - One relevant active session → auto-resume candidate
    - Multiple active sessions → return recent list for user choice
  """

    def __init__(self, store: InMemorySessionStore) -> None:
        self._store = store

    def join_session(
        self,
        repair_session_id: str,
        participant: SessionParticipant,
    ) -> RepairSessionContext:
        self._store.add_participant(participant)
        context = self._store.get_context(repair_session_id)
        if context is None:
            context = RepairSessionContext(repair_session_id=repair_session_id)
            self._store.save_context(context)
        context.last_active_client_device_id = participant.client_device_id
        return self._store.save_context(context)

    def resume_for_user(self, user_id: str) -> RepairSessionContext | None:
        active = self._store.active_contexts_for_user(user_id)
        if len(active) == 1:
            return active[0]
        if not active:
            recent = self._store.recent_contexts(limit=5)
            if len(recent) == 1:
                return recent[0]
        return None

    def recent_sessions_for_user(self, user_id: str, limit: int = 5) -> list[RepairSessionContext]:
        active = self._store.active_contexts_for_user(user_id)
        if active:
            return active[:limit]
        return self._store.recent_contexts(limit=limit)
