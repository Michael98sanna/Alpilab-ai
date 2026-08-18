"""User-local paths that work from source, Desktop shortcut, or frozen EXE."""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def install_dir() -> Path:
    """Directory containing the EXE (frozen) or the repository root (source)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def user_dir() -> Path:
    path = Path.home() / ".alpilab"
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_user_layout() -> dict[str, Path]:
    root = user_dir()
    layout = {
        "root": root,
        "config": root / "config.json",
        "windows_apps": root / "windows_apps.json",
        "logs": root / "logs",
        "data": root / "data",
        "storage": root / "storage",
    }
    layout["logs"].mkdir(parents=True, exist_ok=True)
    layout["data"].mkdir(parents=True, exist_ok=True)
    layout["storage"].mkdir(parents=True, exist_ok=True)
    return layout


def sqlite_path() -> Path:
    return ensure_user_layout()["data"] / "alpilab.db"


def log_dir() -> Path:
    return ensure_user_layout()["logs"]


def storage_dir() -> Path:
    return ensure_user_layout()["storage"]
