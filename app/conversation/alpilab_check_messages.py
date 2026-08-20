"""User-facing messages built only from real Alpilab Check payloads."""

from __future__ import annotations

from typing import Any

from app.conversation.alpilab_check_context import (
    ProductSearchContext,
    ProductSearchItem,
    format_product_label,
)

_PRICE_KEYS = ("price", "prezzo", "cost", "costo", "amount", "importo", "value")
_NAME_KEYS = ("name", "nome", "label", "title", "description", "descrizione")


def format_search_products_response(
    payload: dict[str, Any],
    *,
    context: ProductSearchContext | None = None,
) -> str:
    """
    Format search_products success text (labels only — never listino details).

    0 results → empty message; 1 → ask what to know; >1 → selection list.
    """
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list) or not items:
        return "Non ho trovato prodotti nel listino per questa ricerca."

    source_items: list[ProductSearchItem]
    if context is not None and context.items:
        source_items = list(context.items)
    else:
        source_items = []
        for entry in items:
            if not isinstance(entry, dict):
                continue
            pid = str(entry.get("id") or "").strip()
            if not pid:
                continue
            source_items.append(
                ProductSearchItem(
                    id=pid,
                    brand=str(entry.get("brand") or "").strip(),
                    model=str(entry.get("model") or "").strip(),
                    model_code=str(entry.get("model_code") or "").strip(),
                    name=str(entry.get("name") or "").strip(),
                )
            )

    if not source_items:
        return "Non ho trovato prodotti nel listino per questa ricerca."

    if len(source_items) == 1:
        label = format_product_label(source_items[0])
        return f"Ho trovato {label}. Cosa vuoi sapere?"

    return format_disambiguation_message(source_items)


def format_disambiguation_message(items: list[ProductSearchItem]) -> str:
    """Ask which of several search hits the user meant (no listino data)."""
    lines = [f"Ho trovato {len(items)} modelli:"]
    for i, item in enumerate(items, start=1):
        lines.append(f"{i}. {format_product_label(item)}")
    lines.append("")
    lines.append("Quale intendi?")
    return "\n".join(lines)


def format_selection_confirmation(item: ProductSearchItem) -> str:
    """Confirm model selection without fetching or showing listino data."""
    return f"Perfetto, {format_product_label(item)}."


def _format_price(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # Italian-style decimal comma for money display.
        formatted = f"{value:.2f}".replace(".", ",")
        return f"€{formatted}"
    text = str(value).strip()
    if not text:
        return None
    if text.startswith("€"):
        return text
    return f"€{text}"


def _entry_name(entry: dict[str, Any]) -> str:
    for key in _NAME_KEYS:
        raw = entry.get(key)
        if raw is not None and str(raw).strip():
            return str(raw).strip()
    return ""


def _entry_price(entry: dict[str, Any]) -> str | None:
    for key in _PRICE_KEYS:
        if key in entry:
            return _format_price(entry.get(key))
    return None


def _iter_candidate_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ("services", "parts", "items", "components", "options"):
        value = payload.get(key)
        if isinstance(value, list):
            rows.extend(item for item in value if isinstance(item, dict))
    return rows


def _matches_focus(name: str, focus: str) -> bool:
    lowered = name.lower()
    if focus == "schermo":
        return any(token in lowered for token in ("schermo", "display", "vetro", "lcd", "screen"))
    if focus == "batteria":
        return any(token in lowered for token in ("batteria", "battery", "pila"))
    if focus == "manodopera":
        return "manodopera" in lowered or "mano d'opera" in lowered or "mano d’opera" in lowered
    if focus == "riparazione":
        return "riparaz" in lowered
    if focus == "prezzo":
        return bool(lowered)
    if focus == "compatibile":
        return "compatibil" in lowered
    return False


def _first_price(rows: list[dict[str, Any]]) -> str | None:
    for row in rows:
        price = _entry_price(row)
        if price:
            return price
    return None


def format_get_product_response(
    payload: dict[str, Any],
    *,
    detail_focus: str | None = None,
    product_label: str | None = None,
) -> str:
    """Build assistant text exclusively from tool payload fields for the requested focus."""
    if not isinstance(payload, dict) or not payload:
        return "Non ho trovato dettagli per il prodotto richiesto."

    brand = str(payload.get("brand") or "").strip()
    model = str(payload.get("model") or "").strip()
    payload_label = f"{brand} {model}".strip() if (brand or model) else ""
    raw_name = str(payload.get("name") or "").strip()
    if raw_name and "||" in raw_name:
        raw_name = ""
    product_name = product_label or payload_label or raw_name or "prodotto"
    rows = _iter_candidate_rows(payload)

    if detail_focus is None:
        return (
            f"Ho selezionato {product_name}. "
            "Dimmi cosa vuoi sapere (batteria, schermo, servizi…)."
        )

    if detail_focus == "servizi":
        if not rows:
            return f"Non ho trovato servizi per {product_name}."
        lines: list[str] = []
        for row in rows[:12]:
            name = _entry_name(row)
            price = _entry_price(row)
            if not name:
                continue
            lines.append(f"- {name}: {price}" if price else f"- {name}")
        if not lines:
            return f"Non ho trovato servizi per {product_name}."
        return f"Servizi per {product_name}:\n" + "\n".join(lines)

    if detail_focus == "batteria":
        matches = [row for row in rows if _matches_focus(_entry_name(row), "batteria")]
        price = _first_price(matches)
        if price:
            return f"La batteria per {product_name} costa {price}."
        return f"Non ho trovato il prezzo della batteria per {product_name}."

    if detail_focus == "schermo":
        matches = [row for row in rows if _matches_focus(_entry_name(row), "schermo")]
        price = _first_price(matches)
        if price:
            return f"Lo schermo per {product_name} costa {price}."
        return f"Non ho trovato il prezzo dello schermo per {product_name}."

    if detail_focus in {"manodopera", "riparazione", "compatibile", "prezzo"}:
        if detail_focus == "prezzo":
            matches = rows
            focus_it = "prezzo"
        else:
            matches = [row for row in rows if _matches_focus(_entry_name(row), detail_focus)]
            focus_it = {
                "manodopera": "manodopera",
                "riparazione": "riparazione",
                "compatibile": "compatibile",
            }[detail_focus]
        price = _first_price(matches)
        if price and detail_focus == "prezzo" and len(matches) == 1:
            name = _entry_name(matches[0])
            if name:
                return f"Per {product_name}, {name} costa {price}."
            return f"Per {product_name} il prezzo è {price}."
        if price and detail_focus != "prezzo":
            return f"La {focus_it} per {product_name} costa {price}."
        if detail_focus == "prezzo":
            return (
                f"Dimmi cosa vuoi sapere sul prezzo di {product_name} "
                "(batteria, schermo, servizi…)."
            )
        return f"Non ho trovato il prezzo della {focus_it} per {product_name}."

    return f"Non ho trovato informazioni su {detail_focus} per {product_name}."
