from typing import Any

import httpx

from app.config.logging import get_logger
from app.mcp.schemas import MCPToolDefinition, MCPToolResult

logger = get_logger(__name__)


class MCPTransport:
    def __init__(self, server_url: str, api_key: str = "", timeout: int = 60):
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> bool:
        try:
            self._client = httpx.AsyncClient(
                base_url=self.server_url,
                timeout=httpx.Timeout(self.timeout),
                headers=self._build_headers(),
            )
            response = await self._client.get("/health")
            return response.is_success
        except Exception as exc:
            logger.error("mcp_connect_failed", server_url=self.server_url, error=str(exc))
            return False

    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def list_tools(self) -> list[MCPToolDefinition]:
        if not self._client:
            return []
        try:
            response = await self._client.get("/tools")
            response.raise_for_status()
            data = response.json()
            return [MCPToolDefinition(**tool, server_name=self.server_url) for tool in data.get("tools", [])]
        except Exception as exc:
            logger.error("mcp_list_tools_failed", server_url=self.server_url, error=str(exc))
            return []

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> MCPToolResult:
        if not self._client:
            return MCPToolResult(is_error=True, content=[{"type": "text", "text": "No active connection"}])

        payload = {
            "name": name,
            "arguments": arguments or {},
        }

        try:
            response = await self._client.post("/tools/call", json=payload)
            response.raise_for_status()
            data = response.json()
            return MCPToolResult(**data)
        except httpx.HTTPStatusError as exc:
            logger.error("mcp_tool_call_failed", tool=name, status=exc.response.status_code)
            return MCPToolResult(
                is_error=True,
                content=[{"type": "text", "text": f"HTTP {exc.response.status_code}: {exc.response.text}"}],
            )
        except Exception as exc:
            logger.error("mcp_tool_call_error", tool=name, error=str(exc))
            return MCPToolResult(
                is_error=True,
                content=[{"type": "text", "text": str(exc)}],
            )

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @property
    def is_connected(self) -> bool:
        return self._client is not None
