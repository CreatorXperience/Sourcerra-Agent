from typing import Any

from app.config.logging import get_logger
from app.config.settings import Settings, get_settings
from app.mcp.tools import MCPTool
from app.mcp.transport import MCPTransport
from app.schemas.tools import ToolCallStatus, ToolResult

logger = get_logger(__name__)


class MCPClient:
    def __init__(self, server_url: str, api_key: str = "", timeout: int = 60):
        self.server_url = server_url
        self.transport = MCPTransport(server_url, api_key, timeout)
        self._tools: dict[str, MCPTool] = {}

    async def connect(self) -> bool:
        connected = await self.transport.connect()
        if connected:
            await self._discover_tools()
        return connected

    async def disconnect(self) -> None:
        await self.transport.disconnect()

    async def _discover_tools(self) -> None:
        definitions = await self.transport.list_tools()
        for defn in definitions:
            self._tools[defn.name] = MCPTool(defn)
        logger.info("mcp_tools_discovered", server=self.server_url, count=len(self._tools))

    async def list_tools(self) -> list[MCPTool]:
        return list(self._tools.values())

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> ToolResult:
        result = await self.transport.call_tool(name, arguments)
        if result.is_error:
            return ToolResult(
                status=ToolCallStatus.ERROR,
                error=result.content[0].get("text", "Unknown error") if result.content else "Unknown error",
            )
        return ToolResult(
            status=ToolCallStatus.SUCCESS,
            output=result.content,
        )

    @property
    def is_connected(self) -> bool:
        return self.transport.is_connected


class MCPClientManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._clients: dict[str, MCPClient] = {}

    async def initialize(self) -> None:
        for url in self.settings.MCP_SERVER_URLS:
            client = MCPClient(
                server_url=url,
                timeout=self.settings.MCP_REQUEST_TIMEOUT,
            )
            connected = await client.connect()
            if connected:
                self._clients[url] = client
                logger.info("mcp_client_connected", server=url)
            else:
                logger.warning("mcp_client_connect_failed", server=url)

    async def list_all_tools(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        for client in self._clients.values():
            for tool in await client.list_tools():
                tools.append(tool.to_definition())
        return tools

    async def call_tool(self, tool_name: str, arguments: dict[str, Any], server_name: str | None = None) -> ToolResult:
        if server_name:
            client = self._clients.get(server_name)
            if not client:
                return ToolResult(status=ToolCallStatus.ERROR, error=f"MCP server not found: {server_name}")
            return await client.call_tool(tool_name, arguments)

        for client in self._clients.values():
            tools = await client.list_tools()
            if any(t.name == tool_name for t in tools):
                return await client.call_tool(tool_name, arguments)

        return ToolResult(status=ToolCallStatus.ERROR, error=f"Tool not found: {tool_name}")

    async def shutdown(self) -> None:
        for client in self._clients.values():
            await client.disconnect()
        self._clients.clear()

    def get_client(self, server_url: str) -> MCPClient | None:
        return self._clients.get(server_url)


def get_mcp_manager() -> MCPClientManager:
    settings = get_settings()
    return MCPClientManager(settings)
