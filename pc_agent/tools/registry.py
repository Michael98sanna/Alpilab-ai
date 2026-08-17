"""In-memory local tool registry — only pre-registered tools."""

from __future__ import annotations

from pc_agent.tools.base import LocalToolSpec, execute_safe_test

SAFE_TEST_TOOL_ID = "demo.safe_test"


class LocalToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, LocalToolSpec] = {}
        self._seed()

    def register(self, spec: LocalToolSpec) -> None:
        self._tools[spec.tool_id] = spec

    def get(self, tool_id: str) -> LocalToolSpec | None:
        return self._tools.get(tool_id)

    def list_tools(self) -> list[LocalToolSpec]:
        return list(self._tools.values())

    def _seed(self) -> None:
        self.register(
            LocalToolSpec(
                tool_id=SAFE_TEST_TOOL_ID,
                required_capability="safe_test",
                allowed_argument_keys=frozenset(),
                handler=execute_safe_test,
            )
        )


local_tool_registry = LocalToolRegistry()
