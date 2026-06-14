from collections.abc import Callable
from typing import Any

from app.schemas.tools import ToolDefinition

ToolHandler = Callable[[dict[str, Any]], tuple[list[dict[str, Any]], bool]]


class ToolRegistry:
    def __init__(self):
        self._handlers: dict[str, ToolHandler] = {}
        self._definitions: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        handler: ToolHandler,
        input_schema: dict | None = None,
    ) -> None:
        self._handlers[name] = handler
        self._definitions[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema or {"type": "object", "properties": {}},
        )

    def get_handler(self, name: str) -> ToolHandler | None:
        return self._handlers.get(name)

    def list_definitions(self) -> list[ToolDefinition]:
        return list(self._definitions.values())

    @property
    def count(self) -> int:
        return len(self._handlers)


_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
