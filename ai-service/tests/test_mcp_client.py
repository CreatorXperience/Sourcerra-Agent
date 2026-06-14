import pytest

from app.mcp.client import MCPClient, MCPClientManager
from app.mcp.schemas import MCPToolDefinition, MCPToolResult


@pytest.mark.asyncio
async def test_mcp_client_connect_fails_on_invalid_url() -> None:
    client = MCPClient(server_url="http://invalid.local:9999", timeout=2)
    connected = await client.connect()
    assert connected is False
    await client.disconnect()


@pytest.mark.asyncio
async def test_mcp_client_manager_initializes_empty() -> None:
    from app.config.settings import Settings

    settings = Settings(MCP_SERVER_URLS=[])
    manager = MCPClientManager(settings)
    await manager.initialize()
    tools = await manager.list_all_tools()
    assert tools == []
    await manager.shutdown()


def test_mcp_tool_definition() -> None:
    definition = MCPToolDefinition(
        name="test_tool",
        description="A test tool",
        input_schema={"type": "object", "properties": {}},
        server_name="test-server",
    )
    assert definition.name == "test_tool"
    assert definition.server_name == "test-server"


def test_mcp_tool_result() -> None:
    result = MCPToolResult(
        content=[{"type": "text", "text": "hello"}],
        is_error=False,
    )
    assert result.is_error is False
    assert result.content[0]["text"] == "hello"
