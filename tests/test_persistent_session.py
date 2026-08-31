"""Tests for SQLAlchemy-backed persistent session storage."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.database import Base
from app.models.orm_models import SessionEventModel, SessionModel  # noqa: F401
from app.schemas.session import RepairSessionContext
from app.session.persistent_store import PersistentSessionStore
from app.session.session_manager import SessionManager


@pytest.fixture
def db_session(tmp_path: Path) -> Session:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def _sample_context(session_id: str = "test-1") -> RepairSessionContext:
    return RepairSessionContext(
        repair_session_id=session_id,
        metadata={
            "user_id": "tech-1",
            "device_id": "pc-1",
            "device_model": "iPhone 13",
            "device_brand": "Apple",
        },
    )


def test_save_and_load_session(db_session: Session) -> None:
    store = PersistentSessionStore(db_session)
    session_data = _sample_context("test-1")

    store.save_session("test-1", session_data)
    loaded = store.load_session("test-1")

    assert loaded is not None
    assert loaded.repair_session_id == "test-1"
    assert loaded.metadata["device_model"] == "iPhone 13"
    assert loaded.metadata["device_brand"] == "Apple"


def test_session_survives_restart(tmp_path: Path) -> None:
    db_path = tmp_path / "restart.db"
    url = f"sqlite:///{db_path}"

    engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = factory()
    store = PersistentSessionStore(db)
    store.save_session("test-2", _sample_context("test-2"))
    db.close()

    db2 = factory()
    store2 = PersistentSessionStore(db2)
    loaded = store2.load_session("test-2")

    assert loaded is not None
    assert loaded.repair_session_id == "test-2"
    db2.close()


def test_session_events(db_session: Session) -> None:
    store = PersistentSessionStore(db_session)

    store.add_event("test-1", "CHAT_MESSAGE", {"user": "tech", "text": "ciao"})
    history = store.get_session_history("test-1")

    assert len(history) == 1
    assert history[0]["event_type"] == "CHAT_MESSAGE"
    assert history[0]["payload"]["text"] == "ciao"


def test_soft_delete_hides_session(db_session: Session) -> None:
    store = PersistentSessionStore(db_session)
    store.save_session("test-3", _sample_context("test-3"))

    assert store.delete_session("test-3") is True
    assert store.load_session("test-3") is None
    assert "test-3" not in store.list_active_sessions()


def test_list_active_sessions(db_session: Session) -> None:
    store = PersistentSessionStore(db_session)
    store.save_session("a", _sample_context("a"))
    store.save_session("b", _sample_context("b"))
    store.delete_session("a")

    active = store.list_active_sessions()
    assert active == ["b"]


@pytest.mark.asyncio
async def test_session_manager_resume_and_save(db_session: Session) -> None:
    manager = SessionManager(db_session)
    context = _sample_context("mgr-1")

    await manager.save_and_cache("mgr-1", context)
    manager._sessions.clear()

    resumed = await manager.resume_session("mgr-1")
    assert resumed is not None
    assert resumed.repair_session_id == "mgr-1"


@pytest.mark.asyncio
async def test_session_manager_persists_mutations(db_session: Session) -> None:
    manager = SessionManager(db_session)
    context = _sample_context("mgr-2")
    await manager.save_and_cache("mgr-2", context)

    cached = manager.get_cached_session("mgr-2")
    assert cached is not None
    cached.metadata["note"] = "updated"
    await manager.save_session("mgr-2")

    manager._sessions.clear()
    loaded = await manager.resume_session("mgr-2")
    assert loaded is not None
    assert loaded.metadata["note"] == "updated"
