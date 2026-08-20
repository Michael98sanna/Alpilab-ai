"""Contextual follow-up resolution: SELECTION vs DETAIL for Alpilab Check."""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel

from app.commands.natural_language_parser import MATCH_CONFIDENCE
from app.conversation.alpilab_check_context import (
    ProductSearchContext,
    ProductSearchItem,
    format_product_label,
    mark_product_selected,
)
from app.conversation.alpilab_check_messages import (
    format_disambiguation_message,
    format_selection_confirmation,
)
from app.schemas.commands import Intent
from app.schemas.enums import IntentType

_ORDINAL_LABELS = ("primo", "secondo", "terzo", "quarto", "quinto")


class FollowUpOutcome(str, Enum):
    NO_MATCH = "no_match"
    ACTION = "action"
    SELECTION = "selection"
    CLARIFICATION = "clarification"


class FollowUpResolution(BaseModel):
    outcome: FollowUpOutcome
    intent: Intent | None = None
    message: str | None = None
    detail_focus: str | None = None
    product_index: int | None = None


_GENERAL_CONVERSATION_BLOCKERS = (
    re.compile(r"non si accende", re.I),
    re.compile(r"boot loop", re.I),
    re.compile(r"quanto costa riparare", re.I),
    re.compile(r"riparare\s+(?:un\s+)?(?:iphone|telefono|dispositivo|cellulare)", re.I),
    re.compile(r"con\s+(?:il\s+|lo\s+)?schermo rotto", re.I),
    re.compile(r"\bschermo rotto\b", re.I),
    re.compile(r"\bil mio iphone\b", re.I),
    re.compile(r"\bho un iphone\b", re.I),
    re.compile(r"secondo te", re.I),
    re.compile(r"conviene riparar", re.I),
    re.compile(r"come posso", re.I),
    re.compile(r"come controllo", re.I),
    re.compile(r"pp_vdd", re.I),
    re.compile(r"\bproblema\b", re.I),
    re.compile(r"\bdiagnosi\b", re.I),
    re.compile(r"\bhelp\b", re.I),
    re.compile(r"\baiuto\b", re.I),
)

_ANAPHORA_PATTERNS = (
    re.compile(r"quello che hai trovato", re.I),
    re.compile(r"quello trovato", re.I),
    re.compile(r"questo prodotto", re.I),
    re.compile(r"tra i risultati", re.I),
    re.compile(r"della ricerca", re.I),
    re.compile(r"che hai trovato", re.I),
)

_ORDINAL_PATTERNS: tuple[tuple[re.Pattern[str], int], ...] = (
    (re.compile(r"\b(e\s+)?il\s+quint[oa]\b", re.I), 4),
    (re.compile(r"\b(e\s+)?il\s+quart[oa]\b", re.I), 3),
    (re.compile(r"\b(e\s+)?il\s+terz[oa]\b", re.I), 2),
    (re.compile(r"\b(e\s+)?il\s+second[oa]\b", re.I), 1),
    (re.compile(r"\bquint[oa]\b", re.I), 4),
    (re.compile(r"\bquart[oa]\b", re.I), 3),
    (re.compile(r"\bterz[oa]\b", re.I), 2),
    (re.compile(r"\bsecond[oa]\b", re.I), 1),
    (re.compile(r"\bprim[oa]\b", re.I), 0),
)

_NUMBER_INDEX = re.compile(r"^\s*(\d{1,2})\s*\.?\s*$")

# Specific foci first; prezzo is fallback for generic cost asks.
_DETAIL_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bservizi\b", re.I), "servizi"),
    (re.compile(r"\bschermo\b|\bdisplay\b|\bvetro\b", re.I), "schermo"),
    (re.compile(r"\bbatteria\b", re.I), "batteria"),
    (re.compile(r"\bmanodopera\b", re.I), "manodopera"),
    (re.compile(r"\briparazion", re.I), "riparazione"),
    (re.compile(r"\bcompatibil", re.I), "compatibile"),
    (re.compile(r"\bprezzo\b", re.I), "prezzo"),
)

_FOLLOWUP_PRICE = re.compile(r"quanto\s+(?:costa|viene|costerebbe)|\bcosto\b", re.I)
_FOLLOWUP_SHOW = re.compile(r"fammi vedere", re.I)
_FOLLOWUP_CONTINUATION = re.compile(
    r"^(?:e\s+)?(?:la|il|lo|i|gli|un|una)\s+\w+",
    re.I,
)
_SELECTION_HINTS = (
    re.compile(r"\bintendo\b", re.I),
    re.compile(r"\bscegli(?:o|ere)?\b", re.I),
    re.compile(r"\bprendi\b", re.I),
    re.compile(r"\bquello\b", re.I),
    re.compile(r"\bquesto\b", re.I),
)

_MODEL_AFTER_DEL = re.compile(
    r"\b(?:del|della|dello)\s+(?:prodotto\s+)?(.+)$",
    re.I,
)
_MODEL_AFTER_PER = re.compile(r"^(?:e\s+)?per\s+(?:il\s+|lo\s+|la\s+)?(.+)$", re.I)


def _normalize(text: str) -> str:
    value = text.strip().lower()
    value = value.replace("+", " plus ")
    value = re.sub(r"\s+", " ", value)
    return value.rstrip("?").strip()


def _is_general_conversation(normalized: str) -> bool:
    return any(pattern.search(normalized) for pattern in _GENERAL_CONVERSATION_BLOCKERS)


def _extract_ordinal(normalized: str) -> int | None:
    for pattern, index in _ORDINAL_PATTERNS:
        if pattern.search(normalized):
            return index
    return None


def _extract_number_index(normalized: str) -> int | None:
    m = _NUMBER_INDEX.match(normalized)
    if m:
        value = int(m.group(1))
        return value - 1 if value >= 1 else None
    # Explicit index only ("il 3", "numero 3") — never treat "iPhone 12" as index 12.
    m = re.match(r"^(?:il\s+|numero\s+|n[°o]\s*|#\s*)(\d{1,2})\s*$", normalized, re.I)
    if m:
        value = int(m.group(1))
        return value - 1 if value >= 1 else None
    return None


def _extract_detail_focus(normalized: str) -> str | None:
    for pattern, focus in _DETAIL_PATTERNS:
        if pattern.search(normalized):
            return focus
    if _FOLLOWUP_PRICE.search(normalized):
        return "prezzo"
    return None


def _is_detail_request(normalized: str, detail_focus: str | None) -> bool:
    if detail_focus is not None:
        return True
    if _FOLLOWUP_SHOW.search(normalized):
        return True
    return False


def _has_anaphora(normalized: str) -> bool:
    return any(pattern.search(normalized) for pattern in _ANAPHORA_PATTERNS)


def _item_search_blob(item: ProductSearchItem) -> str:
    return _normalize(
        " ".join(
            part
            for part in (item.brand, item.model, item.model_code, item.name)
            if part
        )
    )


def _strip_selection_prefixes(query: str) -> str:
    value = query
    for prefix in (
        "e per ",
        "per ",
        "e ",
        "quello ",
        "questa ",
        "questo ",
        "il ",
        "la ",
        "lo ",
        "un ",
        "una ",
    ):
        if value.startswith(prefix):
            value = value[len(prefix) :].strip()
    return value


def _extract_model_phrase(normalized: str) -> str | None:
    m = _MODEL_AFTER_DEL.search(normalized)
    if m:
        return _strip_selection_prefixes(m.group(1).strip())
    m = _MODEL_AFTER_PER.match(normalized)
    if m:
        return _strip_selection_prefixes(m.group(1).strip())
    return None


def _match_candidate_indexes(
    query: str,
    context: ProductSearchContext,
) -> list[int]:
    """Return indexes whose brand/model text uniquely fits the user phrase."""
    query = _strip_selection_prefixes(query)
    if not query or len(query) < 2:
        return []

    matches: list[int] = []
    for index, item in enumerate(context.items):
        blob = _item_search_blob(item)
        model = _normalize(item.model)
        label = _normalize(format_product_label(item))
        if not blob:
            continue
        if query == model or query == label or query == blob:
            matches.append(index)
            continue
        if model and (query in model or model in query):
            matches.append(index)
            continue
        tokens = [t for t in re.split(r"[^a-z0-9]+", query) if len(t) >= 3]
        if tokens and all(t in blob for t in tokens):
            matches.append(index)
            continue
    return matches


def _looks_like_product_followup(
    normalized: str,
    *,
    awaiting_selection: bool,
    has_selection: bool,
) -> bool:
    if _extract_ordinal(normalized) is not None:
        return True
    if _extract_number_index(normalized) is not None:
        return True
    if _has_anaphora(normalized):
        return True
    if _extract_detail_focus(normalized) is not None:
        return True
    if _FOLLOWUP_PRICE.search(normalized):
        return True
    if _FOLLOWUP_SHOW.search(normalized):
        return True
    if _FOLLOWUP_CONTINUATION.match(normalized):
        return True
    if normalized.startswith("e "):
        return True
    if awaiting_selection and (
        any(p.search(normalized) for p in _SELECTION_HINTS) or len(normalized) <= 40
    ):
        return True
    if has_selection and len(normalized) <= 40:
        return True
    return False


def _ordinal_clarification(index: int) -> str:
    label = _ORDINAL_LABELS[index] if 0 <= index < len(_ORDINAL_LABELS) else str(index + 1)
    return f"Non ho un {label} prodotto tra i risultati della ricerca."


def _disambiguation_prompt(context: ProductSearchContext) -> str:
    return format_disambiguation_message(context.items)


def _model_not_found_message(phrase: str, context: ProductSearchContext) -> str:
    cleaned = phrase.strip() or "quel modello"
    return (
        f"Non ho trovato {cleaned} tra i risultati della ricerca.\n"
        + _disambiguation_prompt(context)
    )


def _make_get_product_intent(text: str, item: ProductSearchItem) -> Intent:
    return Intent(
        type=IntentType.OPEN_TOOL,
        target="alpilab_check.get_product",
        parameters={"product_id": item.id},
        raw_text=text,
        confidence=MATCH_CONFIDENCE,
    )


def resolve_product_followup(
    text: str,
    context: ProductSearchContext | None,
) -> FollowUpResolution:
    """
    Resolve follow-ups as SELECTION (no tool) or DETAIL (get_product).

    Without context, returns NO_MATCH so normal CONVERSATION routing applies.
    """
    if context is None or not context.items:
        return FollowUpResolution(outcome=FollowUpOutcome.NO_MATCH)

    normalized = _normalize(text)
    if not normalized or _is_general_conversation(normalized):
        return FollowUpResolution(outcome=FollowUpOutcome.NO_MATCH)

    awaiting = bool(context.awaiting_selection)
    has_selection = context.selected_index is not None
    if not _looks_like_product_followup(
        normalized,
        awaiting_selection=awaiting,
        has_selection=has_selection,
    ):
        return FollowUpResolution(outcome=FollowUpOutcome.NO_MATCH)

    detail_focus = _extract_detail_focus(normalized)
    wants_detail = _is_detail_request(normalized, detail_focus)
    ordinal = _extract_ordinal(normalized)
    number_index = _extract_number_index(normalized)

    model_phrase = _extract_model_phrase(normalized)
    name_query = model_phrase if model_phrase else normalized
    # Avoid treating full detail sentences as model names when no del/per phrase.
    if model_phrase is None and wants_detail and (
        ordinal is not None or number_index is not None or has_selection
    ):
        name_matches: list[int] = []
    else:
        name_matches = _match_candidate_indexes(name_query, context)
        # Pure selection short texts: also try stripped query.
        if not name_matches and not wants_detail:
            name_matches = _match_candidate_indexes(
                _strip_selection_prefixes(normalized),
                context,
            )

    selected: int | None = None

    if number_index is not None:
        selected = number_index
    elif ordinal is not None:
        selected = ordinal
    elif len(name_matches) == 1:
        selected = name_matches[0]
    elif len(name_matches) > 1:
        return FollowUpResolution(
            outcome=FollowUpOutcome.CLARIFICATION,
            message=_disambiguation_prompt(context),
        )
    elif model_phrase and not wants_detail:
        # Explicit model not among search hits — do not invent an id.
        return FollowUpResolution(
            outcome=FollowUpOutcome.CLARIFICATION,
            message=_model_not_found_message(model_phrase, context),
        )
    elif awaiting and not wants_detail:
        if (
            _has_anaphora(normalized)
            or _FOLLOWUP_CONTINUATION.match(normalized)
            or normalized.startswith("e ")
        ):
            return FollowUpResolution(
                outcome=FollowUpOutcome.CLARIFICATION,
                message=_disambiguation_prompt(context),
            )
        # Short free-text selection attempt that did not match.
        return FollowUpResolution(
            outcome=FollowUpOutcome.CLARIFICATION,
            message=(
                "Non ho riconosciuto quel modello tra i risultati.\n"
                + _disambiguation_prompt(context)
            ),
        )
    elif has_selection:
        selected = context.selected_index
    elif len(context.items) == 1:
        selected = 0
    elif wants_detail:
        return FollowUpResolution(
            outcome=FollowUpOutcome.CLARIFICATION,
            message=_disambiguation_prompt(context),
        )
    else:
        return FollowUpResolution(outcome=FollowUpOutcome.NO_MATCH)

    if selected is None:
        return FollowUpResolution(outcome=FollowUpOutcome.NO_MATCH)

    if selected < 0 or selected >= len(context.items):
        return FollowUpResolution(
            outcome=FollowUpOutcome.CLARIFICATION,
            message=_ordinal_clarification(selected)
            if selected >= 0
            else "Non ho riconosciuto quel modello tra i risultati.\n"
            + _disambiguation_prompt(context),
            product_index=selected,
        )

    mark_product_selected(context, selected)
    item = context.items[selected]

    if wants_detail:
        focus = detail_focus or "prezzo"
        return FollowUpResolution(
            outcome=FollowUpOutcome.ACTION,
            intent=_make_get_product_intent(text, item),
            detail_focus=focus,
            product_index=selected,
        )

    return FollowUpResolution(
        outcome=FollowUpOutcome.SELECTION,
        message=format_selection_confirmation(item),
        product_index=selected,
    )
