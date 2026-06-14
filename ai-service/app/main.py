import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.agents import register_default_agents
from app.api.router import api_router
from app.config.logging import setup_logging
from app.config.settings import get_settings
from app.core.middleware import setup_middleware
from app.mcp.client import MCPClientManager
from app.services.cache import get_cache_service

_start_time: float = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings)

    register_default_agents()

    cache = get_cache_service()
    await cache.initialize()

    mcp_manager = MCPClientManager(settings)
    await mcp_manager.initialize()
    app.state.mcp_manager = mcp_manager

    yield

    await cache.close()
    await mcp_manager.shutdown()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        lifespan=lifespan,
    )

    setup_middleware(app)
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
