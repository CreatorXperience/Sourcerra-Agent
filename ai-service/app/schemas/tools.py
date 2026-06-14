from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ToolCallStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] = {}
    server_name: str = ""
    enabled: bool = True


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = {}
    server_name: str | None = None


class ToolResult(BaseModel):
    status: ToolCallStatus
    output: Any = None
    error: str | None = None


class ToolCallResponse(BaseModel):
    tool_name: str
    server_name: str
    status: ToolCallStatus
    result: ToolResult
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)


class MCPServerConfig(BaseModel):
    name: str
    url: str = ""
    api_key: str = ""
    enabled: bool = True
    timeout: int = 60
