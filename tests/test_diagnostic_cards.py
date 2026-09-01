"""Tests for diagnostic card persistence service."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.knowledge.embeddings import HashEmbedder
from app.knowledge.knowledge_base import KnowledgeBase
from app.knowledge.models import KnowledgeEntryModel
from app.models.database import Base
from app.models.orm_models import ArchivedDiagnosticCard
from app.services.diagnostic_card_service import DiagnosticCardService


@pytest.fixture
def db_session(tmp_path: Path) -> Session:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'diagnostic_cards.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = factory()
    try:
        yield db
    finally:
        db.close()


def test_create_card(db_session: Session) -> None:
    service = DiagnosticCardService(db_session)
    card = service.create_card("iPhone14,2", "Marco's iPhone", "session-123")
    assert card.id is not None
    assert card.device_id == "iPhone14,2"
    assert card.status == "active"


def test_add_and_get_messages(db_session: Session) -> None:
    service = DiagnosticCardService(db_session)
    card = service.create_card("iPhone14,2", "Test", "session-456")
    service.add_message(card.id, "user", "Display non accende")
    service.add_message(card.id, "assistant", "Controlliamo la batteria...")
    history = service.get_conversation_history(card.id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


def test_update_card_state(db_session: Session) -> None:
    service = DiagnosticCardService(db_session)
    card = service.create_card("iPhone14,2", "Test", "session-789")
    service.update_card_state(
        card.id,
        {
            "current_symptom": "No display",
            "hypothesis": "Battery issue",
            "confidence": 0.85,
        },
    )
    updated = service.get_card(card.id)
    assert updated is not None
    assert updated.current_symptom == "No display"
    assert updated.hypothesis == "Battery issue"
    assert updated.confidence == 0.85


def test_archive_card(db_session: Session) -> None:
    service = DiagnosticCardService(db_session)
    card = service.create_card("iPhone14,2", "Test", "session-archive")
    archived = service.archive_card(
        card.id,
        "success",
        "Battery depleted",
        "Battery replacement",
    )
    assert archived is not None
    assert archived.status == "archived"
    assert archived.outcome == "success"
    assert archived.final_diagnosis == "Battery depleted"


def test_quick_summary(db_session: Session) -> None:
    service = DiagnosticCardService(db_session)
    card = service.create_card("iPhone14,2", "Test", "session-summary")
    service.add_message(card.id, "user", "Test message")
    service.update_card_state(
        card.id,
        {
            "current_symptom": "Heating",
            "hypothesis": "Thermal issue",
            "confidence": 0.75,
        },
    )
    summary = service.get_quick_summary(card.id)
    assert summary is not None
    assert summary["device"] == "Test"
    assert summary["current_symptom"] == "Heating"
    assert summary["messages_count"] == 1
    assert summary["confidence"] == 0.75


def test_get_or_create_card_per_device(db_session: Session) -> None:
    service = DiagnosticCardService(db_session)
    first = service.get_or_create_card("session-multi", "dev-a", "Phone A")
    second = service.get_or_create_card("session-multi", "dev-b", "Phone B")
    assert first.id != second.id
    again = service.get_or_create_card("session-multi", "dev-a", "Phone A")
    assert again.id == first.id


def test_index_in_knowledge_base(db_session: Session) -> None:
    service = DiagnosticCardService(db_session)
    card = service.create_card("iPhone14,2", "Test Phone", "session-kb")
    service.update_card_state(card.id, {"current_symptom": "No power"})
    service.archive_card(card.id, "success", "Dead battery", "Replace battery")

    kb = KnowledgeBase(db_session, embedder=HashEmbedder())
    assert service.index_in_knowledge_base(card.id) is True

    entry = db_session.query(KnowledgeEntryModel).filter_by(id=card.id).first()
    assert entry is not None
    assert "power" in entry.symptom.lower()

    archived = (
        db_session.query(ArchivedDiagnosticCard)
        .filter_by(original_card_id=card.id)
        .first()
    )
    assert archived is not None
    assert archived.indexed_in_kb is True
