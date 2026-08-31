"""Tests for knowledge base indexing and RAG search."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ai.router import SmartAIRouter
from ai.schemas import AIRequest
from app.knowledge.embeddings import HashEmbedder
from app.knowledge.knowledge_base import KnowledgeBase
from app.knowledge.models import KnowledgeEntryModel
from app.knowledge.records import RepairKnowledgeRecord
from app.models.database import Base
from app.schemas.session import RepairSessionContext


@pytest.fixture
def db_session(tmp_path: Path) -> Session:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'knowledge.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = factory()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def kb(db_session: Session) -> KnowledgeBase:
    return KnowledgeBase(db_session, embedder=HashEmbedder())


def _display_repair(session_id: str = "repair-1") -> RepairKnowledgeRecord:
    return RepairKnowledgeRecord(
        session_id=session_id,
        device_model="iPhone 13",
        device_brand="Apple",
        symptoms=["display broken", "no touch"],
        diagnosis="LCD connector broken",
        solution="Replace display cable",
        status="completed",
        repair_duration_min=45,
    )


def _battery_repair(session_id: str = "repair-2") -> RepairKnowledgeRecord:
    return RepairKnowledgeRecord(
        session_id=session_id,
        device_model="Samsung S21",
        device_brand="Samsung",
        symptoms=["battery drain fast", "overheating"],
        diagnosis="Degraded battery cell",
        solution="Replace battery",
        status="completed",
        repair_duration_min=60,
    )


def test_index_repair(kb: KnowledgeBase, db_session: Session) -> None:
    kb.index_repair(_display_repair())

    entry = (
        db_session.query(KnowledgeEntryModel)
        .filter(KnowledgeEntryModel.id == "repair-1")
        .first()
    )
    assert entry is not None
    assert "display" in entry.symptom.lower()
    assert entry.success_rate == 1.0


def test_index_repair_from_session_context(kb: KnowledgeBase, db_session: Session) -> None:
    session = RepairSessionContext(
        repair_session_id="repair-meta-1",
        metadata={
            "device_model": "iPhone 13",
            "device_brand": "Apple",
            "symptoms": ["display broken"],
            "diagnosis": "Broken LCD",
            "solution": "Replace display",
            "status": "completed",
        },
    )
    kb.index_repair(session)

    entry = db_session.query(KnowledgeEntryModel).filter_by(id="repair-meta-1").first()
    assert entry is not None
    assert entry.device == "iPhone 13"


def test_search_similar(kb: KnowledgeBase) -> None:
    kb.index_repair(_display_repair())
    kb.index_repair(_battery_repair())

    results = kb.search_similar("display broken no touch", device="iPhone 13")

    assert len(results) > 0
    assert results[0]["device"] == "iPhone 13"
    assert results[0]["similarity"] > 0.5


def test_get_rag_context(kb: KnowledgeBase) -> None:
    kb.index_repair(_display_repair())

    context = kb.get_rag_context("display broken", device="iPhone 13")

    assert "Casi simili trovati" in context
    assert "Replace display cable" in context


def test_search_similar_empty_database(kb: KnowledgeBase) -> None:
    assert kb.search_similar("display problem") == []


@pytest.mark.asyncio
async def test_router_applies_rag_context(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ai.providers.mock import MockProvider

    kb = KnowledgeBase(db_session, embedder=HashEmbedder())
    kb.index_repair(_display_repair())

    monkeypatch.setattr(
        "app.models.database.SessionLocal",
        lambda: db_session,
    )
    monkeypatch.setattr(db_session, "close", lambda: None)

    router = SmartAIRouter([MockProvider()], enable_rag=True)
    response = await router.generate(
        AIRequest(
            prompt="Cosa posso controllare?",
            symptom="display broken",
            device="iPhone 13",
        ),
        use_cache=False,
    )

    assert response.provider == "mock"
    assert "Casi simili trovati" in response.content
