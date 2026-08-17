"""HTTP API routers."""

from fastapi import APIRouter

from . import health, ai

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
