"""Shared Ollama helpers without provider import cycles."""

from __future__ import annotations

import httpx


def ollama_model_installed(base_url: str, model: str) -> bool:
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{base_url.rstrip('/')}/api/tags")
            response.raise_for_status()
            payload = response.json()
        names = {str(item.get("name", "")).split(":")[0] for item in payload.get("models", [])}
        target = model.split(":")[0]
        return target in names
    except Exception:
        return False
