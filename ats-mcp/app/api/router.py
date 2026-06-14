from fastapi import APIRouter

from app.api.mcp import router as mcp_router

api_router = APIRouter()

api_router.include_router(mcp_router, tags=["MCP"])
