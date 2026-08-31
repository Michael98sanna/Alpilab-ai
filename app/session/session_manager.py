"""Session manager with in-memory cache and SQLAlchemy persistence."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.schemas.session import RepairSessionContext
from app.session.persistent_store import PersistentSessionStore, PersistentSessionStoreError

logger = logging.getLogger(__name__)


class SessionManagerError(Exception):
    """Raised when session manager operations fail."""


class SessionManager:
    """
    Manages repair session contexts with an in-memory cache backed by SQLite.

    Distinct from ``app.realtime.session_manager.RealtimeSessionManager``, which
    handles WebSocket realtime state. This class persists ``RepairSessionContext``.
    """

    def __init__(self, db_session: Session) -> None:
        self.persistent_store = PersistentSessionStore(db_session)
        self._db = db_session
        self._sessions: dict[str, RepairSessionContext] = {}

    def cache_session(self, session_id: str, context: RepairSessionContext) -> None:
        """Put a session in the in-memory cache."""
        if not session_id:
            raise ValueError("session_id is required")
        self._sessions[session_id] = context

    def get_cached_session(self, session_id: str) -> RepairSessionContext | None:
        """Return a cached session without hitting the database."""
        return self._sessions.get(session_id)

    async def resume_session(self, session_id: str) -> RepairSessionContext | None:
        """Load a session from the database and cache it in memory."""
        if not session_id:
            raise ValueError("session_id is required")

        cached = self._sessions.get(session_id)
        if cached is not None:
            return cached

        try:
            session = self.persistent_store.load_session(session_id)
        except PersistentSessionStoreError as exc:
            raise SessionManagerError(
                f"Failed to resume session {session_id}"
            ) from exc

        if session is not None:
            self._sessions[session_id] = session
        return session

    async def save_session(self, session_id: str) -> None:
        """Persist a cached session to the database."""
        if not session_id:
            raise ValueError("session_id is required")

        session = self._sessions.get(session_id)
        if session is None:
            logger.debug("No cached session to save for %s", session_id)
            return

        try:
            self.persistent_store.save_session(session_id, session)
        except PersistentSessionStoreError as exc:
            raise SessionManagerError(
                f"Failed to save session {session_id}"
            ) from exc

    async def save_and_cache(
        self,
        session_id: str,
        context: RepairSessionContext,
    ) -> None:
        """Update cache and persist in one step."""
        self.cache_session(session_id, context)
        await self.save_session(session_id)
