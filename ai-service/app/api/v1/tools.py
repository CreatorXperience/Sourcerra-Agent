from fastapi import APIRouter, Depends

from app.mcp.client import MCPClientManager, get_mcp_manager
from app.schemas.tools import ToolCallRequest, ToolCallResponse, ToolCallStatus, ToolDefinition

router = APIRouter()


@router.get("", response_model=list[ToolDefinition])
async def list_tools(
    mcp: MCPClientManager = Depends(get_mcp_manager),
) -> list[ToolDefinition]:
    return await mcp.list_all_tools()


@router.post("/call", response_model=ToolCallResponse)
async def call_tool(
    request: ToolCallRequest,
    mcp: MCPClientManager = Depends(get_mcp_manager),
) -> ToolCallResponse:
    result = await mcp.call_tool(
        tool_name=request.tool_name,
        arguments=request.arguments,
        server_name=request.server_name,
    )
    return ToolCallResponse(
        tool_name=request.tool_name,
        server_name=request.server_name or "unknown",
        status=ToolCallStatus.SUCCESS if result.error is None else ToolCallStatus.ERROR,
        result=result,
    )
