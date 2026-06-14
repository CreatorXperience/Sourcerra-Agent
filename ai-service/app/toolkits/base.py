from typing import Any

from app.config.settings import Settings, get_settings
from app.mcp.client import MCPClientManager


class BaseToolkit:
    def __init__(self, mcp: MCPClientManager, settings: Settings | None = None):
        self._mcp = mcp
        self._settings = settings or get_settings()

    @classmethod
    def tools(cls) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def call(self, tool_name: str, args: dict[str, Any] | None = None) -> Any:
        return await self._mcp.call_tool(tool_name, args or {})
