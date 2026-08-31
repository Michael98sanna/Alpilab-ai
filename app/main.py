"""
Alpilab AI — FastAPI application with realtime WebSocket support.

Run:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
import sys
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.agents import (
    AgentStatusResponse,
    AgentTestResponse,
    ToolExecuteResponse,
    ToolListResponse,
    execute_3utools_open,
    execute_alpilab_check_open,
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
from app.hub.routes import PairCompleteBody
from app.pairing.service import PairingError
from app.security.audit_middleware import register_audit_logging_middleware


@asynccontextmanager
async def lifespan(_app: FastAPI):
    import os

    from app.models.database import init_db
    from app.realtime.session_manager import realtime_manager
    from app.session.factory import get_session_store, session_store_backend

    init_db()

    if session_store_backend() == "sqlite":
        store = get_session_store()
        realtime_manager.attach_persistence(store)
        realtime_manager.get_or_create_session(
            os.getenv("ALPILAB_DEFAULT_SESSION", "repair-001")
        )
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
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

register_audit_logging_middleware(app)


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
    pairing_token: str | None = Query(None, max_length=256),
) -> None:
    client_host = websocket.client.host if websocket.client else None
    await session_websocket(
        websocket,
        session_id,
        device_id,
        device_type,
        device_name,
        seed_demo=seed_demo,
        pairing_token=pairing_token,
        client_host=client_host,
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


@app.post(
    "/api/v1/sessions/{session_id}/agents/{agent_id}/tools/windows.alpilab_check.open/execute",
    response_model=ToolExecuteResponse,
    tags=["agents"],
)
async def post_alpilab_check_open_execute(
    session_id: str, agent_id: str
) -> ToolExecuteResponse:
    return await execute_alpilab_check_open(session_id, agent_id)


# Legacy AI route (foundation compatibility)
from ai.schemas import AIRequest
from pydantic import BaseModel


class GenerateBody(BaseModel):
    prompt: str


@app.post("/api/v1/ai/generate", tags=["ai"])
def ai_generate(body: GenerateBody) -> dict:
    response = generate_text(AIRequest(prompt=body.prompt))
    return response.model_dump(mode="json")


@app.get("/api/v1/hub/info", tags=["hub"])
def get_hub_info(request: Request) -> dict:
    from app.hub.routes import hub_info

    client_host = request.client.host if request.client else None
    return hub_info(
        port=int(__import__("os").getenv("PORT", "8000")),
        client_host=client_host,
    )


@app.post("/api/v1/pairing/start", tags=["hub"])
def post_pairing_start(request: Request) -> dict:
    from app.hub.routes import start_pairing

    try:
        client_host = request.client.host if request.client else None
        return start_pairing(client_host=client_host)
    except PairingError as exc:
        raise HTTPException(status_code=400, detail=exc.code) from exc


@app.post("/api/v1/pairing/complete", tags=["hub"])
def post_pairing_complete(body: PairCompleteBody) -> dict:
    from app.hub.routes import complete_pairing

    try:
        return complete_pairing(body)
    except PairingError as exc:
        raise HTTPException(status_code=400, detail=exc.code) from exc


@app.get("/api/v1/pairing/clients", tags=["hub"])
def get_pairing_clients() -> dict:
    from app.hub.routes import list_paired

    try:
        return list_paired()
    except PairingError as exc:
        raise HTTPException(status_code=400, detail=exc.code) from exc


@app.delete("/api/v1/pairing/clients/{client_id}", tags=["hub"])
def delete_pairing_client(client_id: str) -> dict:
    from app.hub.routes import revoke_paired

    try:
        return revoke_paired(client_id)
    except PairingError as exc:
        raise HTTPException(status_code=404, detail=exc.code) from exc


@app.post("/api/v1/sessions/{session_id}/photos", tags=["storage"])
async def upload_session_photo(session_id: str, file: UploadFile = File(...)) -> dict:
    from app.storage.photos import save_session_photo

    data = await file.read()
    try:
        return save_session_photo(session_id, file.filename or "photo.jpg", data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/sessions/{session_id}/photos", tags=["storage"])
def get_session_photos(session_id: str) -> dict:
    from app.storage.photos import list_session_photos

    try:
        return {"photos": list_session_photos(session_id)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _frontend_dist() -> Path:
    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        bundled = meipass / "frontend" / "dist"
        if (bundled / "index.html").is_file():
            return bundled
        sidecar = Path(sys.executable).resolve().parent / "frontend" / "dist"
        return sidecar
    return Path(__file__).resolve().parent.parent / "frontend" / "dist"


FRONTEND_DIST = _frontend_dist()


def mount_frontend_spa(application: FastAPI) -> None:
    """Serve the built frontend from / so phones only need port 8000."""
    from fastapi.responses import HTMLResponse

    from app.hub.fallback_ui import HUB_FALLBACK_HTML

    if FRONTEND_DIST.is_dir() and (FRONTEND_DIST / "index.html").is_file():
        assets_dir = FRONTEND_DIST / "assets"
        if assets_dir.is_dir():
            application.mount("/assets", StaticFiles(directory=assets_dir), name="spa-assets")

        @application.get("/{full_path:path}", include_in_schema=False)
        async def spa_fallback(full_path: str) -> FileResponse:
            if full_path.startswith(("api/", "ws/", "docs", "openapi.json", "redoc")):
                raise HTTPException(status_code=404)
            candidate = FRONTEND_DIST / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(FRONTEND_DIST / "index.html")

        return

    @application.get("/", include_in_schema=False)
    async def hub_fallback() -> HTMLResponse:
        return HTMLResponse(HUB_FALLBACK_HTML)


mount_frontend_spa(app)


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
