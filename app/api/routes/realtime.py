"""REST endpoints for realtime session management."""

from pydantic import BaseModel, Field

from app.realtime.session_manager import realtime_manager
from app.realtime.session_state import RealtimeSessionData


class CreateSessionRequest(BaseModel):
    session_id: str | None = None
    seed_demo: bool = False
    label: str | None = None
    device: str | None = None
    issue: str | None = None


class CreateSessionResponse(BaseModel):
    session_id: str
    label: str
    device: str | None = None
    issue: str | None = None


class RealtimeStatusResponse(BaseModel):
    status: str = "ok"
    active_sessions: int
    active_connections: int


def _to_response(data: RealtimeSessionData) -> CreateSessionResponse:
    return CreateSessionResponse(
        session_id=data.session_id,
        label=data.label,
        device=data.device,
        issue=data.issue,
    )


def create_session(body: CreateSessionRequest) -> CreateSessionResponse:
    data = realtime_manager.create_session(
        body.session_id,
        seed_demo=body.seed_demo,
    )
    if body.label:
        data.label = body.label[:120]
    if body.device:
        data.device = body.device[:120]
    if body.issue:
        data.issue = body.issue[:120]
    return _to_response(data)


def get_realtime_status() -> RealtimeStatusResponse:
    return RealtimeStatusResponse(
        active_sessions=len(realtime_manager._sessions),
        active_connections=realtime_manager.connection_count(),
    )
