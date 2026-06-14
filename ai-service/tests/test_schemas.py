from datetime import datetime

from pydantic import ValidationError
import pytest

from app.schemas.agents import AgentConfig, AgentRunRequest, AgentRunResponse, AgentStatus, AgentType
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.health import ComponentStatus, DependencyHealth, HealthCheckResponse
from app.schemas.models import ModelConfig, ModelProvider
from app.schemas.tools import ToolCallRequest, ToolCallResponse, ToolCallStatus, ToolDefinition, ToolResult


def test_success_response() -> None:
    resp = SuccessResponse()
    assert resp.message == "ok"
    assert isinstance(resp.timestamp, datetime)


def test_error_response() -> None:
    resp = ErrorResponse(error="not_found", detail="Resource not found")
    assert resp.error == "not_found"
    assert resp.detail == "Resource not found"


def test_health_check_response() -> None:
    dep = DependencyHealth(name="openrouter", status=ComponentStatus.HEALTHY)
    resp = HealthCheckResponse(
        status=ComponentStatus.HEALTHY,
        dependencies=[dep],
    )
    assert resp.status == ComponentStatus.HEALTHY
    assert len(resp.dependencies) == 1


def test_agent_config_defaults() -> None:
    config = AgentConfig(
        name="test-agent",
        agent_type=AgentType.GENERAL,
    )
    assert config.model == ""
    assert config.max_iterations == 10
    assert config.enable_handoffs is True


def test_agent_run_request_context_defaults() -> None:
    req = AgentRunRequest(agent_name="test", task="do something")
    assert req.context == {}
    assert req.thread_id is None


def test_agent_run_response_default_timestamp() -> None:
    resp = AgentRunResponse(
        run_id="123",
        agent_name="test",
        status=AgentStatus.COMPLETED,
    )
    assert isinstance(resp.timestamp, datetime)


def test_tool_definition() -> None:
    tool = ToolDefinition(
        name="search_candidates",
        description="Search for candidates",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
    )
    assert tool.name == "search_candidates"
    assert tool.enabled is True


def test_tool_call_request() -> None:
    req = ToolCallRequest(
        tool_name="search",
        arguments={"query": "engineer"},
    )
    assert req.tool_name == "search"
    assert req.arguments == {"query": "engineer"}


def test_tool_result_success() -> None:
    result = ToolResult(
        status=ToolCallStatus.SUCCESS,
        output=[{"type": "text", "text": "result"}],
    )
    assert result.error is None


def test_model_config() -> None:
    config = ModelConfig(
        id="openai/gpt-4o",
        provider=ModelProvider.OPENAI,
    )
    assert config.temperature == 0.7
    assert config.supports_function_calling is True


def test_invalid_agent_type() -> None:
    with pytest.raises(ValidationError):
        AgentConfig(name="test", agent_type="invalid_type")


def test_invalid_tool_status() -> None:
    with pytest.raises(ValidationError):
        ToolCallResponse(
            tool_name="test",
            server_name="server",
            status="invalid_status",
            result=ToolResult(status=ToolCallStatus.SUCCESS),
        )
