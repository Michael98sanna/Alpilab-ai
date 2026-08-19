"""Persistent Local Hub configuration under ~/.alpilab (not compiled into the EXE)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from local_hub.paths import ensure_user_layout

DEFAULT_CONFIG: dict[str, Any] = {
    "hub_name": "Alpilab Negozio",
    "host": "0.0.0.0",
    "port": 8000,
    "default_session_id": "repair-001",
    "start_pc_agent": True,
    "start_mdns": True,
    "start_ui": True,
    "start_with_windows": True,
}


def load_hub_config(path: Path | None = None) -> dict[str, Any]:
    layout = ensure_user_layout()
    cfg_path = path or layout["config"]
    data = dict(DEFAULT_CONFIG)
    if cfg_path.is_file():
        try:
            loaded = json.loads(cfg_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data.update(loaded)
        except (OSError, json.JSONDecodeError):
            pass
    else:
        cfg_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
