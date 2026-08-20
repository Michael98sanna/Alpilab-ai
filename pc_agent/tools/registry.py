"""In-memory local tool registry — only pre-registered tools."""

from __future__ import annotations

from pc_agent.tools.base import LocalToolSpec, execute_safe_test
from pc_agent.tools.alpilab_check_handlers import (
    handle_get_invoice,
    handle_get_product,
    handle_search_invoices,
    handle_search_products,
)
from pc_agent.tools.windows_handlers import make_windows_app_handler
from pc_agent.windows_apps.registry import TOOL_ID_TO_APP_ID

SAFE_TEST_TOOL_ID = "demo.safe_test"
WINDOWS_3UTOOLS_OPEN_TOOL_ID = "windows.3utools.open"
WINDOWS_ALPILAB_CHECK_OPEN_TOOL_ID = "windows.alpilab_check.open"
ALPILAB_CHECK_SEARCH_PRODUCTS_TOOL_ID = "alpilab_check.search_products"
ALPILAB_CHECK_GET_PRODUCT_TOOL_ID = "alpilab_check.get_product"
ALPILAB_CHECK_SEARCH_INVOICES_TOOL_ID = "alpilab_check.search_invoices"
ALPILAB_CHECK_GET_INVOICE_TOOL_ID = "alpilab_check.get_invoice"


class LocalToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, LocalToolSpec] = {}
        self._seed()

    def register(self, spec: LocalToolSpec) -> None:
        self._tools[spec.tool_id] = spec

    def get(self, tool_id: str) -> LocalToolSpec | None:
        return self._tools.get(tool_id)

    def list_tools(self) -> list[LocalToolSpec]:
        return list(self._tools.values())

    def _seed(self) -> None:
        self.register(
            LocalToolSpec(
                tool_id=SAFE_TEST_TOOL_ID,
                required_capability="safe_test",
                allowed_argument_keys=frozenset(),
                handler=execute_safe_test,
            )
        )
        for tool_id in TOOL_ID_TO_APP_ID:
            self.register(
                LocalToolSpec(
                    tool_id=tool_id,
                    required_capability="windows_apps",
                    allowed_argument_keys=frozenset(),
                    handler=make_windows_app_handler(tool_id),
                )
            )
        self.register(
            LocalToolSpec(
                tool_id=ALPILAB_CHECK_SEARCH_PRODUCTS_TOOL_ID,
                required_capability="alpilab_check",
                allowed_argument_keys=frozenset({"query", "limit"}),
                handler=handle_search_products,
            )
        )
        self.register(
            LocalToolSpec(
                tool_id=ALPILAB_CHECK_GET_PRODUCT_TOOL_ID,
                required_capability="alpilab_check",
                allowed_argument_keys=frozenset({"product_id"}),
                handler=handle_get_product,
            )
        )
        self.register(
            LocalToolSpec(
                tool_id=ALPILAB_CHECK_SEARCH_INVOICES_TOOL_ID,
                required_capability="alpilab_check",
                allowed_argument_keys=frozenset({"query", "limit"}),
                handler=handle_search_invoices,
            )
        )
        self.register(
            LocalToolSpec(
                tool_id=ALPILAB_CHECK_GET_INVOICE_TOOL_ID,
                required_capability="alpilab_check",
                allowed_argument_keys=frozenset({"invoice_id"}),
                handler=handle_get_invoice,
            )
        )


local_tool_registry = LocalToolRegistry()
