"""Executable tool definitions for controlled PC Agent dispatch."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.enums import ActionRiskLevel, ToolType


FORBIDDEN_REMOTE_ARGUMENT_KEYS = frozenset(
    {
        "path",
        "executable",
        "executable_path",
        "shell_command",
        "command",
        "args",
    }
)


class ExecutableToolSpec(BaseModel):
    """Server-controlled tool registration — clients cannot define tools."""

    tool_id: str = Field(..., min_length=1, max_length=128)
    name: str
    description: str = ""
    version: str = "1.0"
    tool_type: ToolType = ToolType.GENERIC
    risk_level: ActionRiskLevel = ActionRiskLevel.SAFE
    required_capabilities: list[str] = Field(default_factory=list)
    enabled: bool = True
    allowed_argument_keys: frozenset[str] = Field(default_factory=frozenset)


def validate_tool_arguments(
    spec: ExecutableToolSpec,
    arguments: dict[str, Any],
) -> str | None:
    """Return error code if arguments invalid, else None."""
    if not isinstance(arguments, dict):
        return "INVALID_ARGUMENTS"
    keys = frozenset(arguments.keys())
    if keys & FORBIDDEN_REMOTE_ARGUMENT_KEYS:
        return "INVALID_ARGUMENTS"
    if keys != spec.allowed_argument_keys:
        return "INVALID_ARGUMENTS"
    return None


SAFE_TEST_TOOL = ExecutableToolSpec(
    tool_id="demo.safe_test",
    name="Safe Test",
    description="Executes a harmless local test on the PC Agent",
    version="1.0",
    tool_type=ToolType.GENERIC,
    risk_level=ActionRiskLevel.SAFE,
    required_capabilities=["safe_test"],
    enabled=True,
    allowed_argument_keys=frozenset(),
)

WINDOWS_3UTOOLS_OPEN_TOOL = ExecutableToolSpec(
    tool_id="windows.3utools.open",
    name="Open 3uTools",
    description="Open the locally registered 3uTools installation on the PC Agent",
    version="1.0",
    tool_type=ToolType.SOFTWARE_3UTOOLS,
    risk_level=ActionRiskLevel.CONFIRM_REQUIRED,
    required_capabilities=["windows_apps"],
    enabled=True,
    allowed_argument_keys=frozenset(),
)

WINDOWS_ALPILAB_CHECK_OPEN_TOOL = ExecutableToolSpec(
    tool_id="windows.alpilab_check.open",
    name="Open Alpilab Check",
    description="Open the locally configured Alpilab Check application on the PC Agent",
    version="1.0",
    tool_type=ToolType.ALPILAB_CHECK,
    risk_level=ActionRiskLevel.CONFIRM_REQUIRED,
    required_capabilities=["windows_apps"],
    enabled=True,
    allowed_argument_keys=frozenset(),
)

WINDOWS_THERMAL_CAMERA_OPEN_TOOL = ExecutableToolSpec(
    tool_id="windows.thermal_camera.open",
    name="Open Termocamera",
    description="Open the locally configured MIIR thermal-camera software on the PC Agent",
    version="1.0",
    tool_type=ToolType.THERMAL_CAMERA,
    risk_level=ActionRiskLevel.CONFIRM_REQUIRED,
    required_capabilities=["windows_apps"],
    enabled=True,
    allowed_argument_keys=frozenset(),
)

WINDOWS_MICROSCOPE_OPEN_TOOL = ExecutableToolSpec(
    tool_id="windows.microscope.open",
    name="Open Microscopio",
    description="Open the locally configured Mosaic microscope software on the PC Agent",
    version="1.0",
    tool_type=ToolType.MICROSCOPE,
    risk_level=ActionRiskLevel.CONFIRM_REQUIRED,
    required_capabilities=["windows_apps"],
    enabled=True,
    allowed_argument_keys=frozenset(),
)

WINDOWS_BORNEO_OPEN_TOOL = ExecutableToolSpec(
    tool_id="windows.borneo.open",
    name="Open Borneo",
    description=(
        "Open the locally configured Borneo Schematics shortcut/app on the PC Agent. "
        "Auto-login uses Borneo's own saved credentials when enabled there."
    ),
    version="1.0",
    tool_type=ToolType.SOFTWARE_BORNEO,
    risk_level=ActionRiskLevel.CONFIRM_REQUIRED,
    required_capabilities=["windows_apps"],
    enabled=True,
    allowed_argument_keys=frozenset(),
)

ALPILAB_CHECK_SEARCH_PRODUCTS_TOOL = ExecutableToolSpec(
    tool_id="alpilab_check.search_products",
    name="Alpilab Check: Search Products",
    description="Search products through local Alpilab Check bridge v1",
    version="1.0",
    tool_type=ToolType.ALPILAB_CHECK,
    risk_level=ActionRiskLevel.READ_ONLY,
    required_capabilities=["alpilab_check"],
    enabled=True,
    allowed_argument_keys=frozenset({"query", "limit"}),
)

ALPILAB_CHECK_GET_PRODUCT_TOOL = ExecutableToolSpec(
    tool_id="alpilab_check.get_product",
    name="Alpilab Check: Get Product",
    description="Get product details through local Alpilab Check bridge v1",
    version="1.0",
    tool_type=ToolType.ALPILAB_CHECK,
    risk_level=ActionRiskLevel.READ_ONLY,
    required_capabilities=["alpilab_check"],
    enabled=True,
    allowed_argument_keys=frozenset({"product_id"}),
)

ALPILAB_CHECK_SEARCH_INVOICES_TOOL = ExecutableToolSpec(
    tool_id="alpilab_check.search_invoices",
    name="Alpilab Check: Search Invoices",
    description="Search invoices through local Alpilab Check bridge v1",
    version="1.0",
    tool_type=ToolType.ALPILAB_CHECK,
    risk_level=ActionRiskLevel.READ_ONLY,
    required_capabilities=["alpilab_check"],
    enabled=True,
    allowed_argument_keys=frozenset({"query", "limit"}),
)

ALPILAB_CHECK_GET_INVOICE_TOOL = ExecutableToolSpec(
    tool_id="alpilab_check.get_invoice",
    name="Alpilab Check: Get Invoice",
    description="Get invoice details through local Alpilab Check bridge v1",
    version="1.0",
    tool_type=ToolType.ALPILAB_CHECK,
    risk_level=ActionRiskLevel.READ_ONLY,
    required_capabilities=["alpilab_check"],
    enabled=True,
    allowed_argument_keys=frozenset({"invoice_id"}),
)
