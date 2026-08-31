"""SQLAlchemy ORM models for session persistence."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String

from app.models.database import Base


class SessionModel(Base):
    """Persisted repair session context."""

    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)
    device_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    state_json = Column(JSON, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class SessionEventModel(Base):
    """Append-only session event history."""

    __tablename__ = "session_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    payload_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
