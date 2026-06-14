from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.orchestrator import AgentOrchestrator
from app.agents.registry import AgentRegistry
from app.schemas.agents import AgentRunRequest, AgentRunResponse, AgentStatus


@pytest.mark.asyncio
async def test_orchestrator_agent_not_found() -> None:
    mock_registry = MagicMock(spec=AgentRegistry)
    mock_registry.get.return_value = None

    orchestrator = AgentOrchestrator()
    orchestrator._registry = mock_registry

    request = AgentRunRequest(
        agent_name="nonexistent",
        task="Do something",
    )
    response = await orchestrator.run_agent(request)
    assert response.status == AgentStatus.ERROR
    assert response.error is not None
    assert "nonexistent" in response.error


@pytest.mark.asyncio
async def test_orchestrator_known_agent() -> None:
    mock_agent = AsyncMock()
    mock_agent.run.return_value = AgentRunResponse(
        run_id="", agent_name="candidate-matcher",
        status=AgentStatus.COMPLETED,
        output="Matching complete",
    )

    mock_registry = MagicMock(spec=AgentRegistry)
    mock_registry.get.return_value = mock_agent

    orchestrator = AgentOrchestrator()
    orchestrator._registry = mock_registry

    request = AgentRunRequest(
        agent_name="candidate-matcher",
        task="Match candidates for job-123",
    )
    response = await orchestrator.run_agent(request)
    assert response.status == AgentStatus.COMPLETED
    assert response.output == "Matching complete"
