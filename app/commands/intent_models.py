"""Pydantic schemas for semantic intent parsing (Priority 2)."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Semantic intent categories for natural-language commands."""

    OPEN_APPLICATION = "open_application"
    CLOSE_APPLICATION = "close_application"
    RUN_DIAGNOSTIC = "run_diagnostic"
    CLARIFY = "clarify"
    UNKNOWN = "unknown"


class IntentOption(BaseModel):
    """Disambiguation candidate."""

    tool_id: str
    label: str
    confidence: float = Field(ge=0.0, le=1.0)


class IntentResult(BaseModel):
    """Result of semantic intent parsing."""

    intent: IntentType
    tool_id: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    options: list[IntentOption] | None = None
    reasoning: str = ""

    def options_as_dicts(self) -> list[dict[str, Any]] | None:
        if not self.options:
            return None
        return [option.model_dump() for option in self.options]
