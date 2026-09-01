"""SQLAlchemy ORM models for session persistence."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

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


class DiagnosticCard(Base):
    """Active or archived diagnostic repair card for one device."""

    __tablename__ = "diagnostic_cards"

    id = Column(String, primary_key=True)
    session_id = Column(String, index=True, nullable=False)
    device_id = Column(String, index=True, nullable=False)
    device_name = Column(String, nullable=False, default="Unknown")
    status = Column(String, default="active", nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    archived_at = Column(DateTime, nullable=True)

    current_symptom = Column(String, nullable=True)
    diagnostic_stage = Column(String, default="symptom_collection", nullable=False)
    test_results = Column(JSON, default=dict, nullable=False)
    hypothesis = Column(String, nullable=True)
    confidence = Column(Float, default=0.0, nullable=False)
    user_notes = Column(String, nullable=True)

    outcome = Column(String, nullable=True)
    final_diagnosis = Column(String, nullable=True)
    solution_applied = Column(String, nullable=True)


class DiagnosticMessage(Base):
    """Persisted chat message belonging to a diagnostic card."""

    __tablename__ = "diagnostic_messages"

    id = Column(String, primary_key=True)
    card_id = Column(String, ForeignKey("diagnostic_cards.id"), index=True, nullable=False)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    tool_calls = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class ArchivedDiagnosticCard(Base):
    """Snapshot of an archived card prepared for knowledge-base indexing."""

    __tablename__ = "archived_diagnostic_cards"

    id = Column(String, primary_key=True)
    original_card_id = Column(String, index=True, nullable=False)
    device_id = Column(String, index=True, nullable=False)
    symptoms = Column(String, nullable=False, default="")
    diagnosis = Column(String, nullable=False, default="")
    solution = Column(String, nullable=False, default="")
    outcome = Column(String, nullable=False, default="")
    confidence = Column(Float, nullable=False, default=0.0)
    archived_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    indexed_in_kb = Column(Boolean, default=False, nullable=False)
