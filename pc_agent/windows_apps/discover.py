"""Controlled 3uTools path resolution — never execute arbitrary user-supplied names."""

from __future__ import annotations

import os
from pathlib import Path

# Exact filename only. No glob of *.exe, no PATH search of unknown names.
KNOWN_3UTOOLS_NAME = "3uTools.exe"

KNOWN_3UTOOLS_RELATIVE = (
    ("Program Files", "3uTools9", "3uTools.exe"),
    ("Program Files", "3uTools", "3uTools.exe"),
    ("Program Files (x86)", "3uTools9", "3uTools.exe"),
    ("Program Files (x86)", "3uTools", "3uTools.exe"),
)


def _windows_drive() -> Path:
    system_drive = os.getenv("SystemDrive", "C:")
    return Path(system_drive + os.sep)


def discover_3utools_path() -> str | None:
    """Return the first known 3uTools.exe location, or None."""
    root = _windows_drive()
    for parts in KNOWN_3UTOOLS_RELATIVE:
        candidate = root.joinpath(*parts)
        if candidate.is_file() and candidate.name.lower() == KNOWN_3UTOOLS_NAME.lower():
            return str(candidate.resolve())
    return None
