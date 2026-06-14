from typing import Any

from fastapi import APIRouter

from app.schemas.tools import ListToolsResponse, ToolCallContent, ToolCallRequest, ToolCallResponse
from app.tools.registry import get_registry

router = APIRouter()


@router.get("/tools", response_model=ListToolsResponse)
async def list_tools() -> ListToolsResponse:
    registry = get_registry()
    return ListToolsResponse(tools=registry.list_definitions())


@router.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest) -> ToolCallResponse:
    registry = get_registry()
    handler = registry.get_handler(request.name)
    if handler is None:
        return ToolCallResponse(
            content=[ToolCallContent(type="text", text=f"Unknown tool: {request.name}")],
            is_error=True,
        )

    content, is_error = await handler(request.arguments)
    return ToolCallResponse(
        content=[ToolCallContent(**c) if isinstance(c, dict) else ToolCallContent(text=str(c)) for c in content],
        is_error=is_error,
    )


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "healthy", "service": "ats-mcp"}
