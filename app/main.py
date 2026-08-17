"""
Alpilab AI — FastAPI application with realtime WebSocket support.

Run:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.agents import (
    AgentStatusResponse,
    AgentTestResponse,
    ToolExecuteResponse,
    ToolListResponse,
    execute_3utools_open,
    execute_safe_test,
    get_agents_status,
    list_executable_tools,
    send_agent_test,
)
from app.api.routes.ai import generate_text
from app.api.routes.health import get_health
from app.api.routes.realtime import (
    CreateSessionRequest,
    CreateSessionResponse,
    RealtimeStatusResponse,
    create_session,
    get_realtime_status,
)
from app.api.schemas import HealthResponse
from app.api.ws import session_websocket
from app.agent.ws import agent_websocket
from app.api import create_route_registry
from app.core.config import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


app = FastAPI(
    title="Alpilab AI",
    description="Multi-device repair assistant API",
    version="1.0.0-realtime-v1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return get_health()


@app.get("/api/v1/realtime/status", response_model=RealtimeStatusResponse, tags=["realtime"])
def realtime_status() -> RealtimeStatusResponse:
    return get_realtime_status()


@app.post("/api/v1/sessions", response_model=CreateSessionResponse, tags=["realtime"])
def post_create_session(body: CreateSessionRequest) -> CreateSessionResponse:
    return create_session(body)


@app.websocket("/ws/sessions/{session_id}")
async def ws_session(
    websocket: WebSocket,
    session_id: str,
    device_id: str = Query(..., min_length=1, max_length=128),
    device_type: str = Query(..., min_length=1, max_length=32),
    device_name: str = Query("Device", min_length=1, max_length=120),
    seed_demo: bool = Query(False),
) -> None:
    await session_websocket(
        websocket,
        session_id,
        device_id,
        device_type,
        device_name,
        seed_demo=seed_demo,
    )


@app.websocket("/ws/agent/{session_id}")
async def ws_agent(
    websocket: WebSocket,
    session_id: str,
    agent_id: str = Query(..., min_length=1, max_length=128),
) -> None:
    await agent_websocket(websocket, session_id, agent_id)


@app.get("/api/v1/agents/status", response_model=AgentStatusResponse, tags=["agents"])
def agents_status(session_id: str | None = Query(None)) -> AgentStatusResponse:
    return get_agents_status(session_id)


@app.post(
    "/api/v1/sessions/{session_id}/agents/{agent_id}/test",
    response_model=AgentTestResponse,
    tags=["agents"],
)
async def post_agent_test(session_id: str, agent_id: str) -> AgentTestResponse:
    return await send_agent_test(session_id, agent_id)


@app.get("/api/v1/tools", response_model=ToolListResponse, tags=["agents"])
def get_tools() -> ToolListResponse:
    return list_executable_tools()


@app.post(
    "/api/v1/sessions/{session_id}/agents/{agent_id}/tools/demo.safe_test/execute",
    response_model=ToolExecuteResponse,
    tags=["agents"],
)
async def post_safe_test_execute(session_id: str, agent_id: str) -> ToolExecuteResponse:
    return await execute_safe_test(session_id, agent_id)


@app.post(
    "/api/v1/sessions/{session_id}/agents/{agent_id}/tools/windows.3utools.open/execute",
    response_model=ToolExecuteResponse,
    tags=["agents"],
)
async def post_3utools_open_execute(session_id: str, agent_id: str) -> ToolExecuteResponse:
    return await execute_3utools_open(session_id, agent_id)


# Legacy AI route (foundation compatibility)
from ai.schemas import AIRequest
from pydantic import BaseModel


class GenerateBody(BaseModel):
    prompt: str


@app.post("/api/v1/ai/generate", tags=["ai"])
def ai_generate(body: GenerateBody) -> dict:
    response = generate_text(AIRequest(prompt=body.prompt))
    return response.model_dump(mode="json")


def get_registered_routes() -> list[tuple[str, str, str]]:
    """Return (method, path, name) tuples for diagnostics and tests."""
    registry = create_route_registry()
    routes = [(route.method, route.path, route.name) for route in registry.routes()]
    routes.extend(
        [
            ("GET", "/api/v1/realtime/status", "realtime_status"),
            ("POST", "/api/v1/sessions", "create_session"),
            ("GET", "/ws/sessions/{session_id}", "ws_session"),
        ]
    )
    return routes
