"""Deterministic .env loading for development and frozen EXE builds."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Literal, TypedDict

from local_hub.paths import install_dir, is_frozen

logger = logging.getLogger(__name__)

EnvOrigin = Literal[
    "env_var",
    "explicit_argument",
    "executable_dir",
    "build_release",
    "cwd",
    "project_root",
]
EnvOutcome = Literal["found", "not_found", "skipped_not_frozen"]

_LOADED = False
_LOADED_PATH: Path | None = None
_LOADED_SOURCE: str | None = None
_SEARCHED_PATHS: list["EnvSearchEntry"] = []


class EnvSearchEntry(TypedDict):
    """One transparent .env candidate, without exposing environment values."""

    path: str | None
    origin: EnvOrigin
    outcome: EnvOutcome


def _entry(
    path: Path | None,
    origin: EnvOrigin,
    outcome: EnvOutcome,
) -> EnvSearchEntry:
    return {"path": str(path) if path is not None else None, "origin": origin, "outcome": outcome}


def env_search_candidates(*, env_file: Path | str | None = None) -> list[EnvSearchEntry]:
    """Return every .env candidate and its context-specific search outcome."""
    candidates: list[tuple[Path | None, EnvOrigin, bool]] = []

    if env_file is not None:
        candidates.append((Path(env_file).expanduser(), "explicit_argument", False))
    else:
        explicit = os.getenv("ALPILAB_ENV_FILE", "").strip()
        if explicit:
            candidates.append((Path(explicit).expanduser(), "env_var", False))

    frozen = is_frozen()
    if frozen:
        candidates.append((install_dir() / ".env", "executable_dir", False))
        candidates.append((None, "build_release", True))
    else:
        candidates.append((None, "executable_dir", True))
        candidates.append((install_dir() / "build" / "release" / ".env", "build_release", False))

    candidates.append((Path.cwd().resolve() / ".env", "cwd", False))
    if frozen:
        candidates.append((None, "project_root", True))
    else:
        candidates.append((install_dir() / ".env", "project_root", False))

    return [
        _entry(path, origin, "skipped_not_frozen" if skipped else ("found" if path and path.is_file() else "not_found"))
        for path, origin, skipped in candidates
    ]


def env_search_paths() -> list[Path]:
    """Return applicable .env paths, retained for source compatibility."""
    return [
        Path(entry["path"])
        for entry in env_search_candidates()
        if entry["path"] is not None and entry["outcome"] != "skipped_not_frozen"
    ]


def get_env_load_state() -> dict[str, object]:
    return {
        "env_file_loaded": str(_LOADED_PATH) if _LOADED_PATH else None,
        "env_file_loaded_from": _LOADED_SOURCE,
        "env_file_searched": [dict(entry) for entry in _SEARCHED_PATHS],
        "env_file_recommended": str(
            (install_dir() / ".env") if is_frozen() else (install_dir() / "build" / "release" / ".env")
        ),
    }


def load_environment(
    *, force: bool = False, env_file: Path | str | None = None
) -> Path | None:
    """Load the first .env file found in the documented search order."""
    global _LOADED, _LOADED_PATH, _LOADED_SOURCE, _SEARCHED_PATHS

    if _LOADED and not force and env_file is None:
        return _LOADED_PATH

    _SEARCHED_PATHS = env_search_candidates(env_file=env_file)
    if env_file is not None and _SEARCHED_PATHS[0]["outcome"] != "found":
        _LOADED = True
        _LOADED_PATH = None
        _LOADED_SOURCE = None
        raise FileNotFoundError(f"Il file .env indicato non esiste: {_SEARCHED_PATHS[0]['path']}")

    for entry in _SEARCHED_PATHS:
        if entry["outcome"] != "found" or entry["path"] is None:
            continue
        candidate = Path(entry["path"])
        try:
            from dotenv import load_dotenv

            load_dotenv(candidate, override=False)
        except ImportError:
            logger.warning(
                "python-dotenv not installed; cannot load %s from file", candidate
            )
            _LOADED = True
            _LOADED_PATH = candidate.resolve()
            return _LOADED_PATH

        _LOADED = True
        _LOADED_PATH = candidate.resolve()
        _LOADED_SOURCE = entry["origin"]
        logger.info("Ambiente caricato da %s", _LOADED_PATH)
        return _LOADED_PATH

    logger.warning(
        "Nessun file .env trovato. Crealo in: %s",
        get_env_load_state()["env_file_recommended"],
    )
    _LOADED = True
    _LOADED_PATH = None
    _LOADED_SOURCE = None
    return None
