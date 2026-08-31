"""In-memory tool registry for development."""

from app.schemas.enums import ToolStatus, ToolType
from app.tools.base import Tool, ToolCapability
from app.tools.executable import (
    ALPILAB_CHECK_GET_INVOICE_TOOL,
    ALPILAB_CHECK_GET_PRODUCT_TOOL,
    ALPILAB_CHECK_SEARCH_INVOICES_TOOL,
    ALPILAB_CHECK_SEARCH_PRODUCTS_TOOL,
    ExecutableToolSpec,
    SAFE_TEST_TOOL,
    WINDOWS_ALPILAB_CHECK_OPEN_TOOL,
    WINDOWS_MICROSCOPE_OPEN_TOOL,
    WINDOWS_3UTOOLS_OPEN_TOOL,
    WINDOWS_THERMAL_CAMERA_OPEN_TOOL,
)


class ToolRegistry:
    """Registry of known tools without real hardware control."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._executable: dict[str, ExecutableToolSpec] = {}
        self._seed_defaults()
        self._seed_executable()

    def register(self, tool: Tool) -> None:
        self._tools[tool.id] = tool

    def get(self, tool_id: str) -> Tool | None:
        return self._tools.get(tool_id)

    def get_tool(self, tool_id: str) -> Tool | None:
        """Alias used by semantic intent parser."""
        return self.get(tool_id)

    def get_tool_label(self, tool_id: str) -> str:
        """Human-readable label for executable or registered tools."""
        spec = self.get_executable(tool_id)
        if spec is not None:
            return spec.name
        tool = self.get(tool_id)
        if tool is not None:
            return tool.name
        return tool_id

    def get_all_tools(self) -> list[dict[str, str]]:
        """Return matchable tools for semantic intent parsing."""
        catalog: dict[str, dict[str, str]] = {}

        for tool in self.list_tools():
            catalog[tool.id] = {
                "id": tool.id,
                "label": tool.name,
                "description": f"Apri {tool.name} per diagnostica smartphone",
            }

        for spec in self.list_executable():
            catalog[spec.tool_id] = {
                "id": spec.tool_id,
                "label": spec.name,
                "description": spec.description or spec.name,
            }

        return list(catalog.values())

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def set_status(self, tool_id: str, status: ToolStatus) -> Tool | None:
        tool = self._tools.get(tool_id)
        if tool is None:
            return None
        updated = tool.model_copy(update={"status": status})
        self._tools[tool_id] = updated
        return updated

    # --- Executable tools (PC Agent dispatch) ---

    def register_executable(self, spec: ExecutableToolSpec) -> None:
        self._executable[spec.tool_id] = spec

    def get_executable(self, tool_id: str) -> ExecutableToolSpec | None:
        return self._executable.get(tool_id)

    def list_executable(self) -> list[ExecutableToolSpec]:
        return list(self._executable.values())

    def is_enabled(self, tool_id: str) -> bool:
        spec = self._executable.get(tool_id)
        return spec is not None and spec.enabled

    def resolve_executable(self, tool_id: str) -> ExecutableToolSpec | None:
        spec = self._executable.get(tool_id)
        if spec is None or not spec.enabled:
            return None
        return spec

    def _seed_executable(self) -> None:
        self.register_executable(SAFE_TEST_TOOL)
        self.register_executable(WINDOWS_3UTOOLS_OPEN_TOOL)
        self.register_executable(WINDOWS_ALPILAB_CHECK_OPEN_TOOL)
        self.register_executable(WINDOWS_THERMAL_CAMERA_OPEN_TOOL)
        self.register_executable(WINDOWS_MICROSCOPE_OPEN_TOOL)
        self.register_executable(ALPILAB_CHECK_SEARCH_PRODUCTS_TOOL)
        self.register_executable(ALPILAB_CHECK_GET_PRODUCT_TOOL)
        self.register_executable(ALPILAB_CHECK_SEARCH_INVOICES_TOOL)
        self.register_executable(ALPILAB_CHECK_GET_INVOICE_TOOL)

    def _seed_defaults(self) -> None:
        defaults = [
            ("microscope", "Microscopio", ToolType.MICROSCOPE),
            ("thermal_camera", "Termocamera", ToolType.THERMAL_CAMERA),
            ("multimeter", "Multimetro", ToolType.MULTIMETER),
            ("power_supply", "Alimentatore", ToolType.POWER_SUPPLY),
            ("3utools", "3uTools", ToolType.SOFTWARE_3UTOOLS),
            ("borneo", "Borneo", ToolType.SOFTWARE_BORNEO),
            ("zxw", "ZXW", ToolType.SOFTWARE_ZXW),
            ("alpilab_check", "Alpilab Check", ToolType.ALPILAB_CHECK),
        ]
        for tool_id, name, tool_type in defaults:
            self.register(
                Tool(
                    id=tool_id,
                    name=name,
                    tool_type=tool_type,
                    status=ToolStatus.AVAILABLE,
                    capabilities=[ToolCapability(name="open"), ToolCapability(name="close")],
                )
            )


default_tool_registry = ToolRegistry()
