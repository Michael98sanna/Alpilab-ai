"""FastAPI application factory — cloud-first HTTP entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import ai as ai_routes
from app.api.routes import health as health_routes
from app.api.routes import repairs as repair_routes
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description=(
            "Assistente tecnico AI cloud/web per laboratorio di riparazione smartphone. "
            "Progetto separato da Alpilab Check."
        ),
        version="0.1.0",
    )
    app.include_router(health_routes.router)
    app.include_router(ai_routes.router, prefix="/api/ai", tags=["ai"])
    app.include_router(repair_routes.router, prefix="/api/repairs", tags=["repairs"])
    return app


app = create_app()
