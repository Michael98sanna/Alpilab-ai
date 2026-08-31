"""Thread-safe persistent session storage with SQLite backend via SQLAlchemy."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.orm_models import SessionEventModel, SessionModel
from app.schemas.session import RepairSessionContext

logger = logging.getLogger(__name__)


class PersistentSessionStoreError(Exception):
    """Raised when a persistent session operation fails."""


class PersistentSessionStore:
    """Thread-safe persistent session storage with SQLite backend."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def save_session(self, session_id: str, session_data: RepairSessionContext) -> None:
        """Save or update a repair session context."""
        if not session_id:
            raise ValueError("session_id is required")

        state_dict = session_data.model_dump(mode="json", exclude_none=True)
        user_id = session_data.metadata.get("user_id")
        device_id = session_data.metadata.get("device_id")

        try:
            existing = (
                self.db.query(SessionModel)
                .filter(SessionModel.id == session_id)
                .first()
            )

            if existing:
                existing.state_json = state_dict
                existing.updated_at = datetime.now(UTC)
                if user_id is not None:
                    existing.user_id = str(user_id)
                if device_id is not None:
                    existing.device_id = str(device_id)
            else:
                model = SessionModel(
                    id=session_id,
                    user_id=str(user_id) if user_id is not None else None,
                    device_id=str(device_id) if device_id is not None else None,
                    state_json=state_dict,
                )
                self.db.add(model)

            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.exception("Failed to save session %s", session_id)
            raise PersistentSessionStoreError(
                f"Failed to save session {session_id}"
            ) from exc

    def load_session(self, session_id: str) -> RepairSessionContext | None:
        """Load a session from the database."""
        if not session_id:
            raise ValueError("session_id is required")

        model = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.id == session_id,
                SessionModel.deleted_at.is_(None),
            )
            .first()
        )
        if model is None:
            return None

        try:
            return RepairSessionContext.model_validate(model.state_json)
        except Exception as exc:
            logger.exception("Failed to deserialize session %s", session_id)
            raise PersistentSessionStoreError(
                f"Failed to load session {session_id}"
            ) from exc

    def delete_session(self, session_id: str) -> bool:
        """Soft-delete a session."""
        if not session_id:
            raise ValueError("session_id is required")

        model = (
            self.db.query(SessionModel)
            .filter(SessionModel.id == session_id)
            .first()
        )
        if model is None:
            return False

        try:
            model.deleted_at = datetime.now(UTC)
            self.db.commit()
            return True
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.exception("Failed to delete session %s", session_id)
            raise PersistentSessionStoreError(
                f"Failed to delete session {session_id}"
            ) from exc

    def list_active_sessions(self) -> list[str]:
        """Return IDs of non-deleted sessions."""
        sessions = (
            self.db.query(SessionModel.id)
            .filter(SessionModel.deleted_at.is_(None))
            .all()
        )
        return [row[0] for row in sessions]

    def add_event(self, session_id: str, event_type: str, payload: dict[str, Any]) -> None:
        """Append an event to session history."""
        if not session_id:
            raise ValueError("session_id is required")
        if not event_type:
            raise ValueError("event_type is required")

        event = SessionEventModel(
            session_id=session_id,
            event_type=event_type,
            payload_json=payload or {},
        )
        try:
            self.db.add(event)
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.exception("Failed to add event for session %s", session_id)
            raise PersistentSessionStoreError(
                f"Failed to add event for session {session_id}"
            ) from exc

    def get_session_history(
        self,
        session_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Load recent session events, newest first."""
        if not session_id:
            raise ValueError("session_id is required")
        if limit < 1:
            raise ValueError("limit must be >= 1")

        events = (
            self.db.query(SessionEventModel)
            .filter(SessionEventModel.session_id == session_id)
            .order_by(SessionEventModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "event_type": event.event_type,
                "payload": event.payload_json,
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ]

    def cleanup_old_sessions(self, days: int = 90) -> int:
        """Hard-delete sessions soft-deleted more than N days ago."""
        if days < 1:
            raise ValueError("days must be >= 1")

        cutoff = datetime.now(UTC) - timedelta(days=days)
        try:
            deleted = (
                self.db.query(SessionModel)
                .filter(
                    SessionModel.deleted_at.isnot(None),
                    SessionModel.deleted_at < cutoff,
                )
                .delete(synchronize_session=False)
            )
            self.db.commit()
            return int(deleted)
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.exception("Failed to cleanup old sessions")
            raise PersistentSessionStoreError("Failed to cleanup old sessions") from exc
