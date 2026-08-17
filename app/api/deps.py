"""Shared FastAPI dependencies."""

from functools import lru_cache

from ai.router import AIRouter, build_router
from app.core.config import settings
from app.integrations.alpilab_check import AlpilabCheckConnector, MockAlpilabCheckConnector
from app.services.assistant import AssistantService
from hub.mock import MockAlpilabHub
from hub.interface import AlpilabHub


@lru_cache
def get_ai_router() -> AIRouter:
    return build_router(settings.ai_provider)


def get_assistant_service() -> AssistantService:
    return AssistantService(get_ai_router())


def get_check_connector() -> AlpilabCheckConnector:
    return MockAlpilabCheckConnector()


def get_hub() -> AlpilabHub:
    return MockAlpilabHub()
