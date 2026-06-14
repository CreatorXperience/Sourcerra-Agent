from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.agents import register_default_agents
from app.config.settings import Settings
from app.main import create_app


@pytest.fixture(autouse=True)
def _register_agents():
    register_default_agents()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def settings() -> Settings:
    return Settings(
        APP_NAME="Sourcerra AI Service Test",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        OPENROUTER_API_KEY="test-key",
        OPENROUTER_BASE_URL="https://openrouter.ai/api/v1",
        BACKEND_API_BASE_URL="http://localhost:3000/api",
        MCP_SERVER_URLS=[],
    )


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, Any]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def anyio_backend():
    return "asyncio"
