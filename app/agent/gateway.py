"""Agent gateway — coordinates registry, session broadcast, and commands."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.agent.execution_store import tool_execution_store
from app.agent.allowlist import is_command_allowed, reject_reason
from app.agent.payloads import (
    AgentCapabilities,
    AgentInboundMessage,
    AgentOutboundMessage,
    AgentPresencePayload,
    AgentRegistrationPayload,
    CommandEnvelope,
    ResultEnvelope,
)
from app.agent.registry import RegisteredAgent, agent_registry, utc_now
from app.realtime.events import RealtimeEventType
from app.realtime.session_manager import realtime_manager

logger = logging.getLogger(__name__)


def _iso_now() -> str:
    return utc_now().isoformat()


class AgentGateway:
    """Gateway between PC Agents and RepairSession realtime broadcast."""

    async def register_agent(
        self,
        session_id: str,
        registration: AgentRegistrationPayload,
        send_json: Any,
    ) -> RegisteredAgent:
        realtime_manager.get_or_create_session(session_id, seed_demo=False)
        existing = agent_registry.get(session_id, registration.agent_id)
        if existing is not None:
            agent_registry.unregister(session_id, registration.agent_id)

        now = utc_now()
        agent = RegisteredAgent(
            agent_id=registration.agent_id,
            session_id=session_id,
            agent_name=registration.agent_name,
            platform=registration.platform,
            agent_version=registration.agent_version,
            capabilities=registration.capabilities,
            status="ONLINE",
            connected_at=now,
            last_seen=now,
            send_json=send_json,
        )
        agent_registry.register(agent)
        self._set_session_pc_agent(session_id, agent.presence())
        await self._broadcast_agent_event(
            session_id,
            RealtimeEventType.AGENT_CONNECTED,
            agent.presence(),
            registration.agent_id,
        )
        logger.info(
            "Agent registered session=%s agent=%s",
            session_id,
            registration.agent_id,
        )
        return agent

    async def unregister_agent(self, session_id: str, agent_id: str) -> None:
        agent = agent_registry.unregister(session_id, agent_id)
        if agent is None:
            return
        presence = agent.presence()
        presence.online = False
        presence.status = "OFFLINE"
        self._set_session_pc_agent(session_id, None)
        await self._broadcast_agent_event(
            session_id,
            RealtimeEventType.AGENT_DISCONNECTED,
            presence,
            agent_id,
        )
        logger.info("Agent unregistered session=%s agent=%s", session_id, agent_id)

    async def heartbeat(self, session_id: str, agent_id: str) -> bool:
        agent = agent_registry.touch_heartbeat(session_id, agent_id)
        if agent is None:
            return False
        self._set_session_pc_agent(session_id, agent.presence())
        await self._broadcast_agent_event(
            session_id,
            RealtimeEventType.AGENT_HEARTBEAT,
            agent.presence(),
            agent_id,
        )
        return True

    async def send_agent_test(self, session_id: str, agent_id: str) -> CommandEnvelope:
        agent = agent_registry.get(session_id, agent_id)
        if agent is None:
            raise ValueError("agent not found")
        command = CommandEnvelope(
            command_id=str(uuid4()),
            request_id=str(uuid4()),
            type="AGENT_TEST",
            source="alpilab_ai",
            target=agent_id,
            timestamp=_iso_now(),
            payload={},
        )
        envelope = AgentOutboundMessage(type="command", command=command)
        await self._send_to_agent(agent, envelope)
        return command

    async def send_tool_execute(
        self,
        session_id: str,
        agent_id: str,
        tool_id: str,
        arguments: dict[str, Any],
        *,
        request_id: str | None = None,
        command_id: str | None = None,
    ) -> CommandEnvelope:
        agent = agent_registry.get(session_id, agent_id)
        if agent is None:
            raise ValueError("agent not found")

        req_id = request_id or str(uuid4())
        cmd_id = command_id or str(uuid4())

        cached = tool_execution_store.get_completed(req_id)
        if cached is not None:
            return CommandEnvelope(
                command_id=cached.command_id or cmd_id,
                request_id=req_id,
                type="TOOL_EXECUTE",
                source="alpilab_ai",
                target=agent_id,
                timestamp=_iso_now(),
                payload={"tool_id": tool_id, "arguments": arguments},
            )

        command = CommandEnvelope(
            command_id=cmd_id,
            request_id=req_id,
            type="TOOL_EXECUTE",
            source="alpilab_ai",
            target=agent_id,
            timestamp=_iso_now(),
            payload={"tool_id": tool_id, "arguments": arguments},
        )

        await self._emit_tool_audit(
            session_id,
            RealtimeEventType.TOOL_EXECUTION_STARTED,
            {
                "request_id": req_id,
                "command_id": cmd_id,
                "tool_id": tool_id,
                "agent_id": agent_id,
                "source": "alpilab_ai",
                "success": None,
            },
            agent_id,
        )

        envelope = AgentOutboundMessage(type="command", command=command)
        await self._send_to_agent(agent, envelope)
        return command

    async def handle_test_result(
        self,
        session_id: str,
        message: AgentInboundMessage,
    ) -> ResultEnvelope:
        if not message.agent_id or not message.request_id:
            raise ValueError("agent_id and request_id required")
        result = ResultEnvelope(
            request_id=message.request_id,
            command_id=message.command_id,
            agent_id=message.agent_id,
            success=bool(message.success),
            result=message.result or {},
            error=message.error,
            timestamp=message.timestamp or _iso_now(),
        )
        event = realtime_manager.emit(
            session_id,
            RealtimeEventType.AGENT_TEST_RESULT,
            payload=result.model_dump(mode="json"),
            source_client_device_id=message.agent_id,
        )
        await realtime_manager.send_event_ws(session_id, event)
        return result

    async def handle_tool_execute_result(
        self,
        session_id: str,
        message: AgentInboundMessage,
    ) -> ResultEnvelope:
        if not message.agent_id or not message.request_id:
            raise ValueError("agent_id and request_id required")

        result = ResultEnvelope(
            request_id=message.request_id,
            command_id=message.command_id,
            agent_id=message.agent_id,
            tool_id=message.tool_id,
            success=bool(message.success),
            result=message.result or {},
            error=message.error,
            timestamp=message.timestamp or _iso_now(),
        )

        is_new = tool_execution_store.complete(result)

        summary = {
            "request_id": result.request_id,
            "command_id": result.command_id,
            "tool_id": result.tool_id,
            "agent_id": result.agent_id,
            "source": "pc_agent",
            "success": result.success,
            "error": result.error,
            "result_summary": result.result.get("message") if result.result else None,
        }
        await self._emit_tool_audit(
            session_id,
            RealtimeEventType.TOOL_EXECUTION_COMPLETED,
            summary,
            message.agent_id,
        )

        if is_new:
            event = realtime_manager.emit(
                session_id,
                RealtimeEventType.TOOL_EXECUTE_RESULT,
                payload=result.model_dump(mode="json"),
                source_client_device_id=message.agent_id,
            )
            await realtime_manager.send_event_ws(session_id, event)

        return result

    async def handle_inbound_command_request(
        self,
        session_id: str,
        command: CommandEnvelope,
    ) -> None:
        if not is_command_allowed(command.type):
            agent = agent_registry.get(session_id, command.target)
            if agent is None:
                raise ValueError("agent not found")
            envelope = AgentOutboundMessage(
                type="command_rejected",
                message=reject_reason(command.type),
                agent_id=command.target,
                timestamp=_iso_now(),
            )
            await self._send_to_agent(agent, envelope)
            return
        agent = agent_registry.get(session_id, command.target)
        if agent is None:
            raise ValueError("agent not found")
        envelope = AgentOutboundMessage(type="command", command=command)
        await self._send_to_agent(agent, envelope)

    def _set_session_pc_agent(
        self,
        session_id: str,
        presence: AgentPresencePayload | None,
    ) -> None:
        session = realtime_manager.get_session(session_id)
        if session is None:
            return
        session.pc_agent = presence

    async def _broadcast_agent_event(
        self,
        session_id: str,
        event_type: RealtimeEventType,
        presence: AgentPresencePayload,
        agent_id: str,
    ) -> None:
        event = realtime_manager.emit(
            session_id,
            event_type,
            payload=presence.model_dump(mode="json"),
            source_client_device_id=agent_id,
        )
        await realtime_manager.send_event_ws(session_id, event)

    async def _send_to_agent(
        self,
        agent: RegisteredAgent,
        envelope: AgentOutboundMessage,
    ) -> None:
        payload = envelope.model_dump(mode="json")
        result = agent.send_json(payload)
        if asyncio.iscoroutine(result):
            await result

    async def _emit_tool_audit(
        self,
        session_id: str,
        event_type: RealtimeEventType,
        payload: dict[str, Any],
        agent_id: str,
    ) -> None:
        event = realtime_manager.emit(
            session_id,
            event_type,
            payload=payload,
            source_client_device_id=agent_id,
        )
        await realtime_manager.send_event_ws(session_id, event)


agent_gateway = AgentGateway()
