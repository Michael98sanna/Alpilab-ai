"""API route modules."""

from fastapi import APIRouter

from .health import router as health_router
from .ai import router as ai_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
