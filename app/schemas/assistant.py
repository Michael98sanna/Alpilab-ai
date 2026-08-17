"""HTTP schemas for the assistant endpoint."""

from pydantic import BaseModel, Field

from ai.schemas import GenerationResponse


class AssistantAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=8000)


class ProviderInfo(BaseModel):
    name: str
    available: bool
    is_local: bool
    is_cloud: bool
    supports_images: bool
    supports_streaming: bool
    is_mock: bool


class AssistantAskResponse(GenerationResponse):
    """Same contract as the AI layer, exposed over HTTP."""
