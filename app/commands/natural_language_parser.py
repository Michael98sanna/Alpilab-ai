"""Rule-based natural language parser — deterministic, no LLM."""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.commands import Intent
from app.schemas.enums import IntentType

# Rule-based exact/normalized matches use full confidence.
CONFIDENCE_THRESHOLD = 0.8
MATCH_CONFIDENCE = 1.0


class ParseOutcome(str, Enum):
    CONVERSATION = "conversation"
    ACTION_COMMAND = "action_command"
    AMBIGUOUS = "ambiguous"
    COMMAND_NOT_SUPPORTED = "command_not_supported"
    UNKNOWN_APPLICATION = "unknown_application"
    INVALID_COMMAND = "invalid_command"


class NaturalLanguageParseResult(BaseModel):
    outcome: ParseOutcome
    intent: Intent | None = None
    error_code: str | None = None
    clarification: str | None = None
    confidence: float = 0.0


class NaturalLanguageCommandParser:
    """Parse user text into controlled intents — never produces shell/path commands."""

    _FORBIDDEN = (
        re.compile(r"powershell", re.I),
        re.compile(r"cmd\s*/c", re.I),
        re.compile(r"cmd\.exe", re.I),
        re.compile(r"os\.system", re.I),
        re.compile(r"subprocess", re.I),
        re.compile(r"[a-z]:\\", re.I),
        re.compile(r"\.exe\b", re.I),
        re.compile(r"shell\s*=", re.I),
    )

    _OPEN_VERB = re.compile(
        r"^(?:apri|aprimi|avvia|lancia|open|launch|start|"
        r"puoi\s+aprire|puoi\s+avviare)\s+(.+?)\.?$",
        re.I,
    )

    _CLOSE_VERB = re.compile(r"^(?:chiudi|close)\s+(.+)$", re.I)

    _AMBIGUOUS_TARGETS = frozenset(
        {
            "il programma",
            "programma",
            "quello",
            "quello per iphone",
            "quello che usiamo per iphone",
            "quello che usiamo per l iphone",
            "l applicazione",
            "applicazione",
        }
    )

    _UNSUPPORTED_APPS = frozenset({"borneo", "zxw", "chrome", "firefox", "edge"})

    _CONVERSATION_HINTS = (
        "non si accende",
        "boot loop",
        "come posso",
        "come controllo",
        "pp_vdd",
        "diagnostic",
        "diagnosi",
        "problema",
        "help",
        "aiuto",
        "iphone 13",
        "iphone",
        "samsung",
        "display",
        "alimentazione",
    )

    _SEARCH_PRODUCTS = re.compile(
        r"^(?:cerca|trova)\s+(.+?)\s+(?:nel\s+)?(?:listino|catalogo)\.?$",
        re.I,
    )
    _GET_PRODUCT = re.compile(
        r"^(?:mostra|apri|dammi)\s+(?:il\s+)?prodotto\s+([a-z0-9_\-]+)\.?$",
        re.I,
    )
    _SEARCH_INVOICES = re.compile(
        r"^(?:cerca|trova)\s+(.+?)\s+(?:nelle\s+)?fatture\.?$",
        re.I,
    )
    _GET_INVOICE = re.compile(
        r"^(?:mostra|apri|dammi)\s+(?:la\s+)?fattura\s+([a-z0-9_\-]+)\.?$",
        re.I,
    )

    def parse(self, text: str) -> NaturalLanguageParseResult:
        raw = text.strip()
        if not raw:
            return NaturalLanguageParseResult(
                outcome=ParseOutcome.CONVERSATION,
                confidence=0.0,
            )

        normalized = self._normalize(raw)

        for pattern in self._FORBIDDEN:
            if pattern.search(normalized):
                return NaturalLanguageParseResult(
                    outcome=ParseOutcome.INVALID_COMMAND,
                    error_code="INVALID_COMMAND",
                    confidence=MATCH_CONFIDENCE,
                )

        close_match = self._CLOSE_VERB.match(normalized)
        if close_match:
            return NaturalLanguageParseResult(
                outcome=ParseOutcome.COMMAND_NOT_SUPPORTED,
                error_code="COMMAND_NOT_SUPPORTED",
                confidence=MATCH_CONFIDENCE,
            )

        app_target = self._extract_open_target(normalized)
        if app_target is not None:
            return self._resolve_open_target(app_target, raw)

        check_intent = self._extract_alpilab_check_intent(normalized, raw)
        if check_intent is not None:
            return check_intent

        if self._looks_like_conversation(normalized):
            return NaturalLanguageParseResult(
                outcome=ParseOutcome.CONVERSATION,
                confidence=MATCH_CONFIDENCE,
            )

        return NaturalLanguageParseResult(
            outcome=ParseOutcome.CONVERSATION,
            confidence=0.5,
        )

    def _normalize(self, text: str) -> str:
        value = text.strip().lower()
        value = value.replace("3u tools", "3utools")
        value = value.replace("3 u tools", "3utools")
        value = re.sub(r"\s+", " ", value)
        return value.rstrip("?").strip()

    def _extract_open_target(self, normalized: str) -> str | None:
        if normalized == "3utools":
            return "3utools"

        match = self._OPEN_VERB.match(normalized)
        if match:
            return match.group(1).strip()

        return None

    def _resolve_open_target(self, target: str, raw_text: str) -> NaturalLanguageParseResult:
        normalized_target = self._normalize(target)

        if normalized_target in self._AMBIGUOUS_TARGETS or "quello" in normalized_target:
            return NaturalLanguageParseResult(
                outcome=ParseOutcome.AMBIGUOUS,
                error_code="AMBIGUOUS_COMMAND",
                clarification="Quale programma vuoi aprire?",
                confidence=MATCH_CONFIDENCE,
            )

        if normalized_target in self._UNSUPPORTED_APPS:
            return NaturalLanguageParseResult(
                outcome=ParseOutcome.COMMAND_NOT_SUPPORTED,
                error_code="COMMAND_NOT_SUPPORTED",
                confidence=MATCH_CONFIDENCE,
            )

        if normalized_target == "3utools":
            intent = Intent(
                type=IntentType.OPEN_APPLICATION,
                target="3utools",
                raw_text=raw_text,
                confidence=MATCH_CONFIDENCE,
            )
            return NaturalLanguageParseResult(
                outcome=ParseOutcome.ACTION_COMMAND,
                intent=intent,
                confidence=MATCH_CONFIDENCE,
            )

        return NaturalLanguageParseResult(
            outcome=ParseOutcome.UNKNOWN_APPLICATION,
            error_code="UNKNOWN_APPLICATION",
            confidence=MATCH_CONFIDENCE,
        )

    def _looks_like_conversation(self, normalized: str) -> bool:
        if "?" in normalized and not self._OPEN_VERB.match(normalized):
            return True
        return any(hint in normalized for hint in self._CONVERSATION_HINTS)

    def _extract_alpilab_check_intent(
        self, normalized: str, raw_text: str
    ) -> NaturalLanguageParseResult | None:
        m = self._SEARCH_PRODUCTS.match(normalized)
        if m:
            query = m.group(1).strip()
            intent = Intent(
                type=IntentType.OPEN_TOOL,
                target="alpilab_check.search_products",
                parameters={"query": query, "limit": 20},
                raw_text=raw_text,
                confidence=MATCH_CONFIDENCE,
            )
            return NaturalLanguageParseResult(
                outcome=ParseOutcome.ACTION_COMMAND,
                intent=intent,
                confidence=MATCH_CONFIDENCE,
            )

        m = self._GET_PRODUCT.match(normalized)
        if m:
            product_id = m.group(1).strip()
            intent = Intent(
                type=IntentType.OPEN_TOOL,
                target="alpilab_check.get_product",
                parameters={"product_id": product_id},
                raw_text=raw_text,
                confidence=MATCH_CONFIDENCE,
            )
            return NaturalLanguageParseResult(
                outcome=ParseOutcome.ACTION_COMMAND,
                intent=intent,
                confidence=MATCH_CONFIDENCE,
            )

        m = self._SEARCH_INVOICES.match(normalized)
        if m:
            query = m.group(1).strip()
            intent = Intent(
                type=IntentType.OPEN_TOOL,
                target="alpilab_check.search_invoices",
                parameters={"query": query, "limit": 20},
                raw_text=raw_text,
                confidence=MATCH_CONFIDENCE,
            )
            return NaturalLanguageParseResult(
                outcome=ParseOutcome.ACTION_COMMAND,
                intent=intent,
                confidence=MATCH_CONFIDENCE,
            )

        m = self._GET_INVOICE.match(normalized)
        if m:
            invoice_id = m.group(1).strip()
            intent = Intent(
                type=IntentType.OPEN_TOOL,
                target="alpilab_check.get_invoice",
                parameters={"invoice_id": invoice_id},
                raw_text=raw_text,
                confidence=MATCH_CONFIDENCE,
            )
            return NaturalLanguageParseResult(
                outcome=ParseOutcome.ACTION_COMMAND,
                intent=intent,
                confidence=MATCH_CONFIDENCE,
            )

        return None
