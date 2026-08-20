"""Handlers for Alpilab Check bridge-backed read-only tools."""

from __future__ import annotations

from typing import Any

from pc_agent.alpilab_check.bridge_client import AlpilabCheckBridgeClient

_bridge_client: AlpilabCheckBridgeClient | None = None


def configure_alpilab_check_client(client: AlpilabCheckBridgeClient | None = None) -> None:
    global _bridge_client
    _bridge_client = client


def get_alpilab_check_client() -> AlpilabCheckBridgeClient:
    global _bridge_client
    if _bridge_client is None:
        _bridge_client = AlpilabCheckBridgeClient.from_env()
    return _bridge_client


def _ensure_health() -> None:
    get_alpilab_check_client().health()


def handle_search_products(arguments: dict[str, Any]) -> dict[str, Any]:
    _ensure_health()
    query = str(arguments["query"]).strip()
    limit = int(arguments.get("limit", 20))
    return get_alpilab_check_client().search_products(query=query, limit=limit)


def handle_get_product(arguments: dict[str, Any]) -> dict[str, Any]:
    _ensure_health()
    product_id = str(arguments["product_id"]).strip()
    return get_alpilab_check_client().get_product(product_id=product_id)


def handle_search_invoices(arguments: dict[str, Any]) -> dict[str, Any]:
    _ensure_health()
    query = str(arguments["query"]).strip()
    limit = int(arguments.get("limit", 20))
    return get_alpilab_check_client().search_invoices(query=query, limit=limit)


def handle_get_invoice(arguments: dict[str, Any]) -> dict[str, Any]:
    _ensure_health()
    invoice_id = str(arguments["invoice_id"]).strip()
    return get_alpilab_check_client().get_invoice(invoice_id=invoice_id)
