from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.main import create_app
from app.tools.loader import register_all_tools
from app.tools.registry import get_registry


@pytest.fixture(autouse=True)
def _reset_registry():
    registry = get_registry()
    registry._handlers.clear()
    registry._definitions.clear()
    register_all_tools(registry)


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def settings() -> Settings:
    return Settings(
        APP_NAME="ATS MCP Test",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        BACKEND_API_BASE_URL="http://localhost:3000/api",
        BACKEND_API_KEY="test-mcp-key",
    )


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, Any]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_backend_client():
    patch_targets = [
        "app.clients.get_backend_client",
        "app.tools.candidates.get_backend_client",
        "app.tools.jobs.get_backend_client",
        "app.tools.comments.get_backend_client",
        "app.tools.tasks.get_backend_client",
    ]
    client = AsyncMock()
    from unittest.mock import patch
    patches = [patch(t, return_value=client) for t in patch_targets]
    for p in patches:
        p.start()
    yield client
    for p in patches:
        p.stop()


@pytest.fixture
def anyio_backend():
    return "asyncio"
