"""SQLAlchemy database configuration for persistent session storage."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DEFAULT_DATABASE_URL = "sqlite:///./data/alpilab.db"


def _resolve_database_url() -> str:
    return os.getenv("ALPILAB_DATABASE_URL", DEFAULT_DATABASE_URL).strip()


def _ensure_sqlite_parent_dir(url: str) -> None:
    if not url.startswith("sqlite:///"):
        return
    raw_path = url.removeprefix("sqlite:///")
    if raw_path == ":memory:" or raw_path.startswith(":memory:"):
        return
    db_path = Path(raw_path)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)


DATABASE_URL = _resolve_database_url()
_ensure_sqlite_parent_dir(DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db() -> None:
    """Create ORM tables if they do not exist."""
    # Import registers models on Base.metadata.
    from app.models import orm_models  # noqa: F401
    from app.security import models as security_models  # noqa: F401
    from app.knowledge import models as knowledge_models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
