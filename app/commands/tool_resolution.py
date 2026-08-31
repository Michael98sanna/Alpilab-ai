"""Controlled mapping from parsed intents to executable tool IDs."""

from __future__ import annotations

from app.schemas.commands import Intent
from app.schemas.enums import IntentType

# Explicit registry — no dynamic tool_id construction from free text.
APPLICATION_TOOL_MAP: dict[str, str] = {
    "3utools": "windows.3utools.open",
    "alpilab_check": "windows.alpilab_check.open",
    "thermal_camera": "windows.thermal_camera.open",
    "microscope": "windows.microscope.open",
    "alpilab_check.search_products": "alpilab_check.search_products",
    "alpilab_check.get_product": "alpilab_check.get_product",
    "alpilab_check.search_invoices": "alpilab_check.search_invoices",
    "alpilab_check.get_invoice": "alpilab_check.get_invoice",
}

SUPPORTED_OPEN_TARGETS = frozenset(APPLICATION_TOOL_MAP.keys())


def resolve_tool_id(intent: Intent) -> str | None:
    """Map OPEN_APPLICATION intent target to a registered executable tool_id."""
    if intent.type not in {IntentType.OPEN_APPLICATION, IntentType.OPEN_TOOL}:
        return None
    if not intent.target:
        return None
    return APPLICATION_TOOL_MAP.get(intent.target)
