"""In-memory registry for connected PC Agents."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.agent.payloads import AgentCapabilities, AgentConnectionState, AgentPresencePayload


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class RegisteredAgent:
    agent_id: str
    session_id: str
    agent_name: str
    platform: str
    agent_version: str
    capabilities: AgentCapabilities
    status: AgentConnectionState
    connected_at: datetime
    last_seen: datetime
    send_json: Callable[[dict[str, Any]], Any] = field(repr=False)

    def presence(self) -> AgentPresencePayload:
        return AgentPresencePayload(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            platform=self.platform,  # type: ignore[arg-type]
            agent_version=self.agent_version,
            online=self.status == "ONLINE",
            status=self.status,
            capabilities=self.capabilities,
            last_seen=self.last_seen,
        )


class AgentRegistry:
    """Runtime registry of PC Agents keyed by session_id:agent_id."""

    def __init__(self) -> None:
        self._agents: dict[str, RegisteredAgent] = {}

    @staticmethod
    def _key(session_id: str, agent_id: str) -> str:
        return f"{session_id}:{agent_id}"

    def register(self, agent: RegisteredAgent) -> RegisteredAgent:
        key = self._key(agent.session_id, agent.agent_id)
        self._agents[key] = agent
        return agent

    def unregister(self, session_id: str, agent_id: str) -> RegisteredAgent | None:
        key = self._key(session_id, agent_id)
        return self._agents.pop(key, None)

    def get(self, session_id: str, agent_id: str) -> RegisteredAgent | None:
        return self._agents.get(self._key(session_id, agent_id))

    def get_for_session(self, session_id: str) -> RegisteredAgent | None:
        for agent in self._agents.values():
            if agent.session_id == session_id and agent.status == "ONLINE":
                return agent
        return None

    def list_agents(self, session_id: str | None = None) -> list[RegisteredAgent]:
        if session_id is None:
            return list(self._agents.values())
        return [a for a in self._agents.values() if a.session_id == session_id]

    def touch_heartbeat(self, session_id: str, agent_id: str) -> RegisteredAgent | None:
        agent = self.get(session_id, agent_id)
        if agent is None:
            return None
        agent.last_seen = utc_now()
        agent.status = "ONLINE"
        return agent

    def count(self, session_id: str | None = None) -> int:
        return len(self.list_agents(session_id))

    def clear(self) -> None:
        self._agents.clear()


agent_registry = AgentRegistry()
