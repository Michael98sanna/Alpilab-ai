"""Hub-side executable tool specs for iPhone panic log analysis."""

from app.schemas.enums import ActionRiskLevel, ToolType
from app.tools.executable import ExecutableToolSpec

IPHONE_PANIC_LOG_CHECK_TOOL = ExecutableToolSpec(
    tool_id="iphone.panic_log.check",
    name="iPhone Panic Log Check",
    description="Check connected iPhone and locate the latest panic-full log",
    version="1.0",
    tool_type=ToolType.GENERIC,
    risk_level=ActionRiskLevel.READ_ONLY,
    required_capabilities=["iphone_panic"],
    enabled=True,
    allowed_argument_keys=frozenset(),
)

IPHONE_PANIC_LOG_ANALYZE_TOOL = ExecutableToolSpec(
    tool_id="iphone.panic_log.analyze",
    name="iPhone Panic Log Analyze",
    description="Parse and analyze the latest iPhone panic log on demand",
    version="1.0",
    tool_type=ToolType.GENERIC,
    risk_level=ActionRiskLevel.SAFE,
    required_capabilities=["iphone_panic"],
    enabled=True,
    allowed_argument_keys=frozenset({"force_reanalyze"}),
)
