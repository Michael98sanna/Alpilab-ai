"""Mock command parser mapping natural language to intents."""

import re

from app.schemas.commands import Intent
from app.schemas.enums import IntentType


class MockCommandParser:
    """Rule-based parser for foundation testing (not production NLP)."""

    _TOOL_ALIASES = {
        "termocamera": "thermal_camera",
        "thermal camera": "thermal_camera",
        "borneo": "borneo",
        "3utools": "3utools",
        "zxw": "zxw",
        "microscopio": "microscope",
        "multimetro": "multimeter",
        "alimentatore": "power_supply",
        "alpilab check": "alpilab_check",
    }

    def parse(self, text: str) -> Intent:
        normalized = text.strip().lower()

        if normalized in {"fermati", "stop", "pausa", "pause"}:
            return Intent(type=IntentType.STOP, raw_text=text)
        if normalized in {"continua diagnosi", "continua", "resume"}:
            return Intent(type=IntentType.CONTINUE_DIAGNOSIS, raw_text=text)
        if normalized in {"riprendi", "resume session"}:
            return Intent(type=IntentType.RESUME, raw_text=text)
        if "reset" in normalized and "diagnosi" in normalized:
            return Intent(type=IntentType.RESET_DIAGNOSTIC_FLOW, raw_text=text)
        if normalized.startswith("salva") and "misura" in normalized:
            return Intent(type=IntentType.SAVE_MEASUREMENT, raw_text=text)
        if "schema" in normalized:
            return Intent(type=IntentType.SHOW_SCHEMA, raw_text=text)
        if normalized.startswith("scatta") or "foto" in normalized:
            return Intent(type=IntentType.CAPTURE_IMAGE, raw_text=text)

        open_match = re.match(r"^(apri|open)\s+(.+)$", normalized)
        if open_match:
            target = self._resolve_tool(open_match.group(2))
            return Intent(
                type=IntentType.OPEN_TOOL,
                target=target,
                raw_text=text,
            )

        close_match = re.match(r"^(chiudi|close)\s+(.+)$", normalized)
        if close_match:
            target = self._resolve_tool(close_match.group(2))
            return Intent(
                type=IntentType.CLOSE_TOOL,
                target=target,
                raw_text=text,
            )

        return Intent(type=IntentType.CONVERSATION, raw_text=text)

    def _resolve_tool(self, phrase: str) -> str:
        phrase = phrase.strip()
        return self._TOOL_ALIASES.get(phrase, phrase.replace(" ", "_"))
