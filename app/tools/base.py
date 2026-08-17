"""Generic tool abstraction for bench instruments and software."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.enums import ToolStatus, ToolType


class ToolCapability(BaseModel):
    """One capability exposed by a tool."""

    name: str
    description: str | None = None


class Tool(BaseModel):
    """Generic tool descriptor (microscope, Borneo, multimeter, etc.)."""

    id: str
    name: str
    tool_type: ToolType
    status: ToolStatus = ToolStatus.UNKNOWN
    capabilities: list[ToolCapability] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolController(ABC):
    """Future controller for a specific tool instance."""

    @abstractmethod
    def get_tool(self) -> Tool:
        raise NotImplementedError

    @abstractmethod
    def open(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> bool:
        raise NotImplementedError
