"""In-memory tool registry for development."""

from app.schemas.enums import ToolStatus, ToolType
from app.tools.base import Tool, ToolCapability
from app.tools.executable import ExecutableToolSpec, SAFE_TEST_TOOL, WINDOWS_3UTOOLS_OPEN_TOOL


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
