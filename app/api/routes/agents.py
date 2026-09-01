"""REST endpoints for PC Agent management."""

from pydantic import BaseModel, Field

from app.agent.gateway import agent_gateway
from app.agent.payloads import AgentPresencePayload, ResultEnvelope
from app.agent.registry import agent_registry
from app.agent.tool_executor import ToolExecutionError, tool_execution_service
from app.tools.registry import default_tool_registry


class AgentStatusResponse(BaseModel):
    status: str = "ok"
    session_id: str | None = None
    agents_online: int = 0
    agents: list[AgentPresencePayload] = Field(default_factory=list)


class AgentTestRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=128)


class AgentTestResponse(BaseModel):
    status: str = "sent"
    request_id: str
    command_id: str
    agent_id: str


class ToolExecuteResponse(BaseModel):
    status: str = "completed"
    request_id: str
    command_id: str | None = None
    agent_id: str
    tool_id: str
    success: bool
    result: dict = Field(default_factory=dict)
    error: str | None = None


class ToolListResponse(BaseModel):
    status: str = "ok"
    tools: list[dict] = Field(default_factory=list)


class ToolExecuteRequest(BaseModel):
    force_reanalyze: bool = False


def get_agents_status(session_id: str | None = None) -> AgentStatusResponse:
    agents = agent_registry.list_agents(session_id)
    online = [a for a in agents if a.status == "ONLINE"]
    return AgentStatusResponse(
        session_id=session_id,
        agents_online=len(online),
        agents=[a.presence() for a in agents],
    )


async def send_agent_test(session_id: str, agent_id: str) -> AgentTestResponse:
    command = await agent_gateway.send_agent_test(session_id, agent_id)
    return AgentTestResponse(
        request_id=command.request_id,
        command_id=command.command_id,
        agent_id=agent_id,
    )


def list_executable_tools() -> ToolListResponse:
    tools = [
        {
            "tool_id": t.tool_id,
            "name": t.name,
            "description": t.description,
            "version": t.version,
            "risk_level": t.risk_level.value,
            "required_capabilities": t.required_capabilities,
            "enabled": t.enabled,
        }
        for t in default_tool_registry.list_executable()
    ]
    return ToolListResponse(tools=tools)


async def execute_safe_test(session_id: str, agent_id: str) -> ToolExecuteResponse:
    return await _execute_tool(session_id, agent_id, "demo.safe_test")


async def execute_3utools_open(session_id: str, agent_id: str) -> ToolExecuteResponse:
    return await _execute_tool(session_id, agent_id, "windows.3utools.open")


async def execute_alpilab_check_open(session_id: str, agent_id: str) -> ToolExecuteResponse:
    return await _execute_tool(session_id, agent_id, "windows.alpilab_check.open")


async def execute_thermal_camera_open(
    session_id: str, agent_id: str
) -> ToolExecuteResponse:
    return await _execute_tool(session_id, agent_id, "windows.thermal_camera.open")


async def execute_microscope_open(session_id: str, agent_id: str) -> ToolExecuteResponse:
    return await _execute_tool(session_id, agent_id, "windows.microscope.open")


async def execute_borneo_open(session_id: str, agent_id: str) -> ToolExecuteResponse:
    return await _execute_tool(session_id, agent_id, "windows.borneo.open")


async def execute_iphone_panic_check(session_id: str, agent_id: str) -> ToolExecuteResponse:
    return await _execute_tool(session_id, agent_id, "iphone.panic_log.check")


async def execute_iphone_panic_analyze(
    session_id: str,
    agent_id: str,
    body: ToolExecuteRequest | None = None,
) -> ToolExecuteResponse:
    request = body or ToolExecuteRequest()
    return await _execute_tool(
        session_id,
        agent_id,
        "iphone.panic_log.analyze",
        {"force_reanalyze": request.force_reanalyze},
    )


async def _execute_tool(
    session_id: str,
    agent_id: str,
    tool_id: str,
    arguments: dict | None = None,
) -> ToolExecuteResponse:
    args = arguments if arguments is not None else {}
    try:
        result = await tool_execution_service.execute_tool(
            session_id,
            agent_id,
            tool_id,
            args,
        )
    except ToolExecutionError as exc:
        return ToolExecuteResponse(
            status="error",
            request_id="",
            agent_id=agent_id,
            tool_id=tool_id,
            success=False,
            error=exc.error_code,
        )

    return ToolExecuteResponse(
        request_id=result.request_id,
        command_id=result.command_id,
        agent_id=result.agent_id,
        tool_id=result.tool_id or tool_id,
        success=result.success,
        result=result.result,
        error=result.error,
    )
