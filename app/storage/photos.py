"""Local photo storage for RepairSession — no cloud, no editor."""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from local_hub.paths import storage_dir

_SAFE_SESSION = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def session_photo_dir(session_id: str) -> Path:
    if not _SAFE_SESSION.match(session_id):
        raise ValueError("invalid session_id")
    path = storage_dir() / session_id / "photos"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_session_photo(session_id: str, filename: str, data: bytes) -> dict:
    if len(data) > 8 * 1024 * 1024:
        raise ValueError("file too large")
    suffix = Path(filename).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".jpg"
    stored_name = f"{uuid4().hex[:12]}{suffix}"
    dest = session_photo_dir(session_id) / stored_name
    dest.write_bytes(data)
    return {
        "session_id": session_id,
        "filename": stored_name,
        "bytes": len(data),
        "path": str(dest),
    }


def list_session_photos(session_id: str) -> list[str]:
    folder = session_photo_dir(session_id)
    return sorted(p.name for p in folder.iterdir() if p.is_file())
