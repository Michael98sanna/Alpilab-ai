"""Minimal per-session context for Alpilab Check product search follow-ups."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

SOURCE_TOOL_SEARCH_PRODUCTS = "alpilab_check.search_products"


class ProductSearchItem(BaseModel):
    id: str
    brand: str = ""
    model: str = ""
    model_code: str = ""
    name: str = ""


class ProductSearchContext(BaseModel):
    """Search hits plus optional selected product for follow-up detail queries."""

    items: list[ProductSearchItem] = Field(default_factory=list)
    created_at: datetime | None = None
    source_tool: str = SOURCE_TOOL_SEARCH_PRODUCTS
    awaiting_selection: bool = False
    selected_index: int | None = None
    selected_product_id: str | None = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_product_label(item: ProductSearchItem) -> str:
    """User-facing label: brand + model only (never technical id)."""
    brand = (item.brand or "").strip()
    model = (item.model or "").strip()
    if brand and model:
        return f"{brand} {model}"
    if model:
        return model
    if brand:
        return brand
    name = (item.name or "").strip()
    if name and "||" not in name:
        return name
    code = (item.model_code or "").strip()
    if code:
        return code
    return "prodotto"


def build_product_search_context(payload: dict[str, Any]) -> ProductSearchContext | None:
    """
    Build context from search_products result.

    Returns None when there are zero valid items (clears previous context).
    Retains id/brand/model/model_code only — no raw payload, secrets, or paths.
    """
    raw_items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(raw_items, list):
        return None

    items: list[ProductSearchItem] = []
    for entry in raw_items:
        if not isinstance(entry, dict):
            continue
        product_id = str(entry.get("id") or "").strip()
        if not product_id:
            continue
        brand = str(entry.get("brand") or "").strip()
        model = str(entry.get("model") or "").strip()
        model_code = str(entry.get("model_code") or "").strip()
        name = str(entry.get("name") or "").strip()
        items.append(
            ProductSearchItem(
                id=product_id,
                brand=brand,
                model=model,
                model_code=model_code,
                name=name,
            )
        )

    if not items:
        return None

    multi = len(items) > 1
    if multi:
        return ProductSearchContext(
            items=items,
            created_at=_utc_now(),
            source_tool=SOURCE_TOOL_SEARCH_PRODUCTS,
            awaiting_selection=True,
            selected_index=None,
            selected_product_id=None,
        )

    return ProductSearchContext(
        items=items,
        created_at=_utc_now(),
        source_tool=SOURCE_TOOL_SEARCH_PRODUCTS,
        awaiting_selection=False,
        selected_index=0,
        selected_product_id=items[0].id,
    )


def apply_product_search_context(
    session: Any,
    payload: dict[str, Any],
) -> None:
    """Replace session product context with the latest search result."""
    session.product_search_context = build_product_search_context(payload)


def mark_product_selected(context: ProductSearchContext, index: int) -> None:
    """Record which search hit the user chose (selection only — no listino fetch)."""
    if 0 <= index < len(context.items):
        context.selected_index = index
        context.selected_product_id = context.items[index].id
        context.awaiting_selection = False


def selected_item(context: ProductSearchContext) -> ProductSearchItem | None:
    if context.selected_index is None:
        return None
    if 0 <= context.selected_index < len(context.items):
        return context.items[context.selected_index]
    return None
