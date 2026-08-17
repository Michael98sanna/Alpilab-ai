"""API schemas for AI endpoints."""

from pydantic import BaseModel, Field

from ai.schemas import RequestKind


class AskRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    kind: RequestKind = RequestKind.GENERAL
    image_paths: list[str] = Field(default_factory=list)


class AskResponse(BaseModel):
    content: str
    provider: str
    kind: RequestKind
