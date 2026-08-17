"""Persistent local agent identity."""

from __future__ import annotations

import json
import os
from uuid import uuid4


def load_or_create_agent_id(identity_path: str) -> str:
    """
    Load a stable agent_id from local storage or create a new one.

    Uses a random UUID — not hostname/MAC.
    """
    if os.path.isfile(identity_path):
        try:
            with open(identity_path, encoding="utf-8") as fh:
                data = json.load(fh)
            agent_id = str(data.get("agent_id", "")).strip()
            if agent_id:
                return agent_id
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    agent_id = f"agent-{uuid4().hex[:12]}"
    os.makedirs(os.path.dirname(identity_path) or ".", exist_ok=True)
    with open(identity_path, "w", encoding="utf-8") as fh:
        json.dump({"agent_id": agent_id}, fh, indent=2)
    return agent_id
