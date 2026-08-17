"""FastAPI application factory.

The HTTP API is the primary interface for web, tablet and smartphone clients.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.routes.assistant import router as assistant_router
from app.api.routes.health import router as health_router
from app.core.config import settings

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_STATIC = FRONTEND_DIR / "static"


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "Assistente tecnico AI per laboratorio di riparazione smartphone. "
            "Fase foundation: API + MockProvider, senza provider cloud né hardware."
        ),
    )

    origins = settings.cors_origin_list
    if origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    application.include_router(health_router, prefix="/api/v1")
    application.include_router(assistant_router, prefix="/api/v1")

    @application.get("/", include_in_schema=False)
    def frontend_index() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")

    if FRONTEND_STATIC.is_dir():
        application.mount(
            "/static",
            StaticFiles(directory=str(FRONTEND_STATIC)),
            name="static",
        )

    return application


app = create_app()
