"""Select in-memory or SQLite session store."""

from __future__ import annotations

import os
from functools import lru_cache

from app.session.sqlite_store import DEFAULT_DB_PATH, SQLiteSessionStore
from app.session.store import InMemorySessionStore


def session_store_backend() -> str:
    return os.getenv("ALPILAB_SESSION_STORE", "memory").strip().lower()


@lru_cache(maxsize=1)
def get_session_store():
    backend = session_store_backend()
    if backend == "sqlite":
        path = os.getenv("ALPILAB_SQLITE_PATH", str(DEFAULT_DB_PATH))
        return SQLiteSessionStore(path)
    return InMemorySessionStore()


def reset_session_store_cache() -> None:
    get_session_store.cache_clear()
