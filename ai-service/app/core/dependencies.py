from fastapi import Request

from app.config.settings import Settings, get_settings
from app.mcp.client import MCPClientManager
from app.providers.openrouter import OpenRouterProvider


def get_settings_from_request(request: Request) -> Settings:
    return get_settings()


async def get_mcp_client_manager(request: Request) -> MCPClientManager:
    settings = get_settings()
    manager = MCPClientManager(settings)
    return manager


async def get_llm_provider(request: Request) -> OpenRouterProvider:
    settings = get_settings()
    return OpenRouterProvider(settings)
