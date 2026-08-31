"""SQLAlchemy models for the repair knowledge base."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text

from app.models.database import Base


class KnowledgeEntryModel(Base):
    """Indexed completed repair case for RAG retrieval."""

    __tablename__ = "knowledge_base"

    id = Column(String, primary_key=True)
    device = Column(String, index=True, nullable=False)
    brand = Column(String, nullable=False, default="")
    symptom = Column(String, index=True, nullable=False)
    diagnosis = Column(String, nullable=False, default="")
    solution = Column(String, nullable=False, default="")
    technical_notes = Column(Text, nullable=True)
    embedding_vector = Column(JSON, nullable=False)
    repair_duration_min = Column(Integer, nullable=True)
    success_rate = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
