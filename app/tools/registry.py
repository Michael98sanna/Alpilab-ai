"""In-memory tool registry for development."""

from app.schemas.enums import ToolStatus, ToolType
from app.tools.base import Tool, ToolCapability


class ToolRegistry:
    """Registry of known tools without real hardware control."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._seed_defaults()

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
