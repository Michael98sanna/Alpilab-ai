"""REST endpoints for PC Agent management."""

from pydantic import BaseModel, Field

from app.agent.gateway import agent_gateway
from app.agent.payloads import AgentPresencePayload, ResultEnvelope
from app.agent.registry import agent_registry


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
