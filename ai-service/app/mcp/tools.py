from typing import Any

from app.config.logging import get_logger
from app.mcp.schemas import MCPToolDefinition

logger = get_logger(__name__)


class MCPTool:
    def __init__(self, definition: MCPToolDefinition):
        self._def = definition

    @property
    def name(self) -> str:
        return self._def.name

    @property
    def description(self) -> str:
        return self._def.description

    @property
    def input_schema(self) -> dict:
        return self._def.input_schema

    @property
    def server_name(self) -> str:
        return self._def.server_name

    def to_openai_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }

    def to_agents_sdk_tool(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema,
        }

    def to_definition(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "server_name": self.server_name,
        }
