"""Centralized audit logging."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.security.models import AuditLogModel

logger = logging.getLogger(__name__)


class AuditLogError(Exception):
    """Raised when persisting an audit log entry fails."""


class AuditLogger:
    """Persist and query audit log entries."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def log_action(
        self,
        user_id: str | None,
        action_type: str,
        status: str = "SUCCESS",
        tool_id: str | None = None,
        risk_level: str = "LOW",
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
        error_message: str | None = None,
    ) -> AuditLogModel:
        """Record an auditable action."""
        if not action_type:
            raise ValueError("action_type is required")

        log_entry = AuditLogModel(
            user_id=user_id,
            session_id=session_id,
            action_type=action_type,
            tool_id=tool_id,
            status=status,
            risk_level=risk_level,
            action_metadata=metadata or {},
            error_message=error_message,
        )
        try:
            self.db.add(log_entry)
            self.db.commit()
            self.db.refresh(log_entry)
            return log_entry
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.exception("Failed to write audit log for action %s", action_type)
            raise AuditLogError(f"Failed to write audit log for {action_type}") from exc

    def get_session_audit(self, session_id: str) -> list[dict[str, Any]]:
        """Return chronological audit entries for a session."""
        if not session_id:
            raise ValueError("session_id is required")

        logs = (
            self.db.query(AuditLogModel)
            .filter(AuditLogModel.session_id == session_id)
            .order_by(AuditLogModel.created_at)
            .all()
        )
        return [self._serialize_entry(entry) for entry in logs]

    def get_user_audit(self, user_id: str, days: int = 30) -> list[dict[str, Any]]:
        """Return recent audit entries for a user."""
        if not user_id:
            raise ValueError("user_id is required")
        if days < 1:
            raise ValueError("days must be >= 1")

        cutoff = datetime.now(UTC) - timedelta(days=days)
        logs = (
            self.db.query(AuditLogModel)
            .filter(
                AuditLogModel.user_id == user_id,
                AuditLogModel.created_at >= cutoff,
            )
            .order_by(AuditLogModel.created_at.desc())
            .all()
        )
        return [
            {
                "action_type": entry.action_type,
                "session_id": entry.session_id,
                "status": entry.status,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in logs
        ]

    @staticmethod
    def _serialize_entry(entry: AuditLogModel) -> dict[str, Any]:
        return {
            "action_type": entry.action_type,
            "tool_id": entry.tool_id,
            "status": entry.status,
            "risk_level": entry.risk_level,
            "created_at": entry.created_at.isoformat(),
            "metadata": entry.action_metadata,
        }
