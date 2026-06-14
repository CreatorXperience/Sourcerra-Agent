from pydantic import BaseModel, Field


class MCPServerInfo(BaseModel):
    name: str
    url: str
    connected: bool = False


class MCPToolDefinition(BaseModel):
    name: str
    description: str = ""
    input_schema: dict = Field(default_factory=dict)
    server_name: str = ""


class MCPToolCall(BaseModel):
    tool_name: str
    arguments: dict = Field(default_factory=dict)


class MCPToolResult(BaseModel):
    content: list[dict] = Field(default_factory=list)
    is_error: bool = False
    meta: dict = Field(default_factory=dict)
