from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict = Field(default_factory=dict)


class ListToolsResponse(BaseModel):
    tools: list[ToolDefinition] = Field(default_factory=list)


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict = Field(default_factory=dict)


class ToolCallContent(BaseModel):
    type: str = "text"
    text: str = ""


class ToolCallResponse(BaseModel):
    content: list[ToolCallContent] = Field(default_factory=list)
    is_error: bool = False
