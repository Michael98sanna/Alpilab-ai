"""WebSocket handler for PC Agent connections."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from app.agent.gateway import agent_gateway
from app.agent.payloads import (
    AgentCapabilities,
    AgentInboundMessage,
    AgentOutboundMessage,
    AgentRegistrationPayload,
)

logger = logging.getLogger(__name__)


async def agent_websocket(
    websocket: WebSocket,
    session_id: str,
    agent_id: str,
) -> None:
    """
    WebSocket handler: /ws/agent/{session_id}

    Query param: agent_id (required)
    First message must be type=register with full registration payload.
    """
    await websocket.accept()
    registered_agent_id: str | None = None

    async def send_json(payload: dict[str, Any]) -> None:
        await websocket.send_json(payload)

    try:
        while True:
            raw_text = await websocket.receive_text()
            if len(raw_text) > 8192:
                await send_json(
                    AgentOutboundMessage(
                        type="error",
                        message="payload too large",
                    ).model_dump(mode="json")
                )
                continue
            try:
                raw = json.loads(raw_text)
            except json.JSONDecodeError:
                await send_json(
                    AgentOutboundMessage(
                        type="error",
                        message="invalid json",
                    ).model_dump(mode="json")
                )
                continue
            if not isinstance(raw, dict):
                await send_json(
                    AgentOutboundMessage(
                        type="error",
                        message="invalid payload",
                    ).model_dump(mode="json")
                )
                continue

            message = AgentInboundMessage.model_validate(raw)

            if message.type == "register":
                registration = AgentRegistrationPayload(
                    agent_id=message.agent_id or agent_id,
                    agent_name=message.agent_name or "ALPILAB-PC",
                    platform=message.platform or "windows",
                    agent_version=message.agent_version or "0.1.0",
                    capabilities=message.capabilities or AgentCapabilities(),
                    status=message.status or "ONLINE",
                )
                await agent_gateway.register_agent(session_id, registration, send_json)
                registered_agent_id = registration.agent_id
                await send_json(
                    AgentOutboundMessage(
                        type="registered",
                        message="REGISTERED",
                        agent_id=registration.agent_id,
                    ).model_dump(mode="json")
                )
                continue

            if registered_agent_id is None:
                await send_json(
                    AgentOutboundMessage(
                        type="error",
                        message="register required before other messages",
                    ).model_dump(mode="json")
                )
                continue

            if message.type == "heartbeat":
                ok = await agent_gateway.heartbeat(session_id, registered_agent_id)
                if not ok:
                    await send_json(
                        AgentOutboundMessage(
                            type="error",
                            message="agent not registered",
                        ).model_dump(mode="json")
                    )
                    continue
                await send_json(AgentOutboundMessage(type="heartbeat_ack").model_dump(mode="json"))
                continue

            if message.type == "agent_test_result":
                message.agent_id = registered_agent_id
                await agent_gateway.handle_test_result(session_id, message)
                continue

            await send_json(
                AgentOutboundMessage(
                    type="error",
                    message="unsupported message type",
                ).model_dump(mode="json")
            )

    except WebSocketDisconnect:
        logger.info(
            "Agent WebSocket disconnected session=%s agent=%s",
            session_id,
            registered_agent_id or agent_id,
        )
    finally:
        if registered_agent_id:
            await agent_gateway.unregister_agent(session_id, registered_agent_id)
