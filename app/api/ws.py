"""WebSocket endpoint for multi-device realtime sessions."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from app.realtime.payloads import WsEnvelope
from app.realtime.session_manager import realtime_manager

logger = logging.getLogger(__name__)


async def session_websocket(
    websocket: WebSocket,
    session_id: str,
    device_id: str,
    device_type: str,
    device_name: str,
    seed_demo: bool = False,
) -> None:
    """
    WebSocket handler: /ws/sessions/{session_id}

    Query params: device_id, device_type, device_name, seed_demo (optional)
    """
    await websocket.accept()

    async def send_json(payload: dict[str, Any]) -> None:
        await websocket.send_json(payload)

    try:
        _, snapshot = await realtime_manager.connect_device(
            session_id,
            device_id,
            device_type,
            device_name,
            seed_demo=seed_demo,
        )
        realtime_manager.register_ws(session_id, device_id, send_json)

        await send_json(
            WsEnvelope(
                type="snapshot",
                payload=snapshot.model_dump(mode="json"),
            ).model_dump(mode="json")
        )

        while True:
            raw_text = await websocket.receive_text()
            if len(raw_text) > 8192:
                await send_json(
                    WsEnvelope(type="error", message="payload too large").model_dump(
                        mode="json"
                    )
                )
                continue
            try:
                raw = json.loads(raw_text)
            except json.JSONDecodeError:
                await send_json(
                    WsEnvelope(type="error", message="invalid json").model_dump(
                        mode="json"
                    )
                )
                continue
            if not isinstance(raw, dict):
                await send_json(
                    WsEnvelope(type="error", message="invalid payload").model_dump(
                        mode="json"
                    )
                )
                continue
            await realtime_manager.handle_client_message(session_id, device_id, raw)
            await send_json(WsEnvelope(type="ack").model_dump(mode="json"))

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected session=%s device=%s", session_id, device_id)
    except ValueError as exc:
        logger.warning("WebSocket validation error: %s", exc)
        try:
            await send_json(
                WsEnvelope(type="error", message=str(exc)).model_dump(mode="json")
            )
        except Exception:
            pass
    finally:
        await realtime_manager.disconnect_device(session_id, device_id)
