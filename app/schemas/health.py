"""Health and runtime metadata returned by the API."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    phase: str
    provider: str
    environment: str
