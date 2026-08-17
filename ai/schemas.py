"""Request and response contracts for the AI layer.

Application code should depend on these types, not on a specific provider.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class RequestKind(str, Enum):
    """Hint for future routing. Only TEXT and IMAGE are used in this phase."""

    TEXT = "text"
    IMAGE = "image"
    DIAGNOSIS = "diagnosis"
    GUIDED_CHECK = "guided_check"


class ImageInput(BaseModel):
    """Reference to an image. Bytes are not required at this stage."""

    filename: str
    content_type: str | None = None
    storage_key: str | None = None
    caption: str | None = None


class AIRequest(BaseModel):
    prompt: str
    kind: RequestKind = RequestKind.TEXT
    images: list[ImageInput] = Field(default_factory=list)
    preferred_provider: str | None = None
    prefer_local: bool = False
    prefer_low_cost: bool = False

    @property
    def has_images(self) -> bool:
        return bool(self.images)


class AIResponse(BaseModel):
    text: str
    provider_name: str
    is_mock: bool = False
    request_kind: RequestKind = RequestKind.TEXT
