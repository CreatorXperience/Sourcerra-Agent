from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.candidate_summary import CandidateSummaryAgent
from app.schemas.agents import AgentConfig, AgentRunResponse, AgentStatus, AgentType
from app.schemas.tools import ToolCallStatus, ToolResult
from app.schemas.workflows import CandidateSummaryOutput
from app.workflows.candidate_summary import CandidateSummaryWorkflow


@pytest.fixture(autouse=True)
def _mock_openai_client() -> None:
    with patch("app.agents.candidate_summary.AsyncOpenAI") as mock_client:
        mock_client.return_value = MagicMock()
        yield


@pytest.fixture
def agent() -> CandidateSummaryAgent:
    return CandidateSummaryAgent(
        AgentConfig(name="candidate-summarizer", agent_type=AgentType.CANDIDATE_SUMMARY),
    )


class TestCandidateSummaryAgent:
    async def test_agent_registered(self) -> None:
        from app.agents import register_default_agents
        from app.agents.registry import AgentRegistry

        registry = AgentRegistry()
        register_default_agents(registry)
        registered = registry.get("candidate-summarizer")

        assert registered is not None
        assert registered.config.name == "candidate-summarizer"
        assert registered.config.agent_type == AgentType.CANDIDATE_SUMMARY

    @patch("app.agents.candidate_summary.Runner.run")
    async def test_run_returns_structured_output(self, mock_run: MagicMock, agent: CandidateSummaryAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = CandidateSummaryOutput(
            candidate_name="Alice Smith",
            overview="Senior engineer with 8 years of experience in Python and AWS.",
            recruiter_observations=["Strong communication skills", "Excellent culture fit"],
            open_action_items=["Schedule technical interview", "Request references"],
            recommended_next_action="Proceed to technical screen",
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="some candidate data")

        assert result.status == AgentStatus.COMPLETED
        assert result.agent_name == "candidate-summarizer"
        assert result.error is None
        assert "Alice Smith" in (result.output or "")

    @patch("app.agents.candidate_summary.Runner.run")
    async def test_run_with_empty_comments_and_tasks(self, mock_run: MagicMock, agent: CandidateSummaryAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = CandidateSummaryOutput(
            candidate_name="Bob Jones",
            overview="Mid-level backend developer.",
            recruiter_observations=[],
            open_action_items=[],
            recommended_next_action="Review application",
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="candidate data without comments or tasks")

        assert result.status == AgentStatus.COMPLETED
        assert result.agent_name == "candidate-summarizer"
        assert result.output is not None

    @patch("app.agents.candidate_summary.Runner.run")
    async def test_run_strict_separation(self, mock_run: MagicMock, agent: CandidateSummaryAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = CandidateSummaryOutput(
            candidate_name="Carol",
            overview="QA engineer.",
            recruiter_observations=["Detail-oriented", "Finds edge cases quickly"],
            open_action_items=["Prepare test environment"],
            recommended_next_action="Assign to test automation project",
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="all candidate data")

        assert result.status == AgentStatus.COMPLETED
        parsed = result.output if result.output else ""
        assert "recruiter_observations" in parsed
        assert "open_action_items" in parsed
        assert "recommended_next_action" in parsed

    @patch("app.agents.candidate_summary.Runner.run")
    async def test_run_loads_prompt_template(self, mock_run: MagicMock, agent: CandidateSummaryAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = CandidateSummaryOutput(
            candidate_name="Test", overview="", recruiter_observations=[],
            open_action_items=[], recommended_next_action="",
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="data")

        assert result.status == AgentStatus.COMPLETED
        args, _ = mock_run.call_args
        openai_agent = args[0]
        instructions = openai_agent.instructions
        assert "Candidate Overview" in instructions
        assert "Recruiter Observations" in instructions
        assert "Open Action Items" in instructions
        assert "Recommended Next Action" in instructions


class TestCandidateSummaryWorkflow:
    async def test_missing_agent_returns_error(self) -> None:
        with patch("app.workflows.candidate_summary.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = None
            mock_reg.return_value = mock_registry

            workflow = CandidateSummaryWorkflow()
            result = await workflow.execute(candidate_id="cand-1")

        assert result.status == AgentStatus.ERROR
        assert result.error and "not registered" in result.error

    async def test_missing_mcp_manager_returns_error(self) -> None:
        with patch("app.workflows.candidate_summary.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = MagicMock()
            mock_reg.return_value = mock_registry

            workflow = CandidateSummaryWorkflow()
            result = await workflow.execute(candidate_id="cand-1", mcp_manager=None)

        assert result.status == AgentStatus.ERROR
        assert result.error and "not available" in result.error

    async def test_happy_path_all_data_available(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.run.return_value = AgentRunResponse(
            run_id="run-1",
            agent_name="candidate-summarizer",
            status=AgentStatus.COMPLETED,
            output='{"candidate_name":"Alice","overview":"Senior engineer","recruiter_observations":["Good communicator"],"open_action_items":["Schedule interview"],"recommended_next_action":"Proceed"}',
        )

        with patch("app.workflows.candidate_summary.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_agent
            mock_reg.return_value = mock_registry

            mock_mcp = AsyncMock()

            async def mock_call_tool(name: str, args: dict) -> ToolResult:
                if name == "ats_get_candidate":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": '{"name":"Alice","stage":"INTERVIEW"}'}])
                if name == "ats_get_candidate_comments":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": "Strong communication skills"}])
                if name == "ats_get_candidate_tasks":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": "Schedule interview"}])
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown tool")

            mock_mcp.call_tool = mock_call_tool

            workflow = CandidateSummaryWorkflow()
            result = await workflow.execute(candidate_id="cand-1", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.COMPLETED
        assert result.output and "Alice" in result.output
        mock_agent.run.assert_called_once()

    async def test_graceful_missing_comments_and_tasks(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.run.return_value = AgentRunResponse(
            run_id="run-2",
            agent_name="candidate-summarizer",
            status=AgentStatus.COMPLETED,
            output='{"candidate_name":"Bob","overview":"Developer","recruiter_observations":[],"open_action_items":[],"recommended_next_action":"Review"}',
        )

        with patch("app.workflows.candidate_summary.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_agent
            mock_reg.return_value = mock_registry

            mock_mcp = AsyncMock()

            async def mock_call_tool(name: str, args: dict) -> ToolResult:
                if name == "ats_get_candidate":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": '{"name":"Bob","stage":"APPLIED"}'}])
                if name == "ats_get_candidate_comments":
                    return ToolResult(status=ToolCallStatus.ERROR, error="Not found")
                if name == "ats_get_candidate_tasks":
                    return ToolResult(status=ToolCallStatus.ERROR, error="Not found")
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown")

            mock_mcp.call_tool = mock_call_tool

            workflow = CandidateSummaryWorkflow()
            result = await workflow.execute(candidate_id="cand-1", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.COMPLETED

    async def test_partial_data_comments_only(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.run.return_value = AgentRunResponse(
            run_id="run-3",
            agent_name="candidate-summarizer",
            status=AgentStatus.COMPLETED,
            output='{"candidate_name":"Carol","overview":"QA","recruiter_observations":["Detail-oriented"],"open_action_items":[],"recommended_next_action":"Review"}',
        )

        with patch("app.workflows.candidate_summary.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_agent
            mock_reg.return_value = mock_registry

            mock_mcp = AsyncMock()

            async def mock_call_tool(name: str, args: dict) -> ToolResult:
                if name == "ats_get_candidate":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": '{"name":"Carol"}'}])
                if name == "ats_get_candidate_comments":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": "Detail-oriented"}])
                if name == "ats_get_candidate_tasks":
                    return ToolResult(status=ToolCallStatus.ERROR, error="Tasks not available")
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown")

            mock_mcp.call_tool = mock_call_tool

            workflow = CandidateSummaryWorkflow()
            result = await workflow.execute(candidate_id="cand-1", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.COMPLETED

    async def test_partial_data_tasks_only(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.run.return_value = AgentRunResponse(
            run_id="run-4",
            agent_name="candidate-summarizer",
            status=AgentStatus.COMPLETED,
            output='{"candidate_name":"Dan","overview":"Dev","recruiter_observations":[],"open_action_items":["Review resume"],"recommended_next_action":"Review"}',
        )

        with patch("app.workflows.candidate_summary.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_agent
            mock_reg.return_value = mock_registry

            mock_mcp = AsyncMock()

            async def mock_call_tool(name: str, args: dict) -> ToolResult:
                if name == "ats_get_candidate":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": '{"name":"Dan"}'}])
                if name == "ats_get_candidate_comments":
                    return ToolResult(status=ToolCallStatus.ERROR, error="No comments")
                if name == "ats_get_candidate_tasks":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": "Review resume"}])
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown")

            mock_mcp.call_tool = mock_call_tool

            workflow = CandidateSummaryWorkflow()
            result = await workflow.execute(candidate_id="cand-1", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.COMPLETED


class TestBuildInput:
    def test_all_data_present(self) -> None:
        workflow = CandidateSummaryWorkflow()
        result = workflow._build_input(
            candidate_raw=[{"text": '{"name":"Alice","stage":"INTERVIEW"}'}],
            comments_raw=[{"text": "Great communicator"}],
            tasks_raw=[{"text": "Schedule follow-up"}],
        )

        assert "CANDIDATE PROFILE" in result
        assert "RECRUITER COMMENTS" in result
        assert "CANDIDATE TASKS" in result
        assert "Alice" in result
        assert "Great communicator" in result
        assert "Schedule follow-up" in result

    def test_all_data_missing(self) -> None:
        workflow = CandidateSummaryWorkflow()
        result = workflow._build_input(None, None, None)

        assert "(not available)" in result
        assert "(none)" in result

    def test_candidate_only(self) -> None:
        workflow = CandidateSummaryWorkflow()
        result = workflow._build_input(
            candidate_raw=[{"text": "Charlie, new applicant"}],
            comments_raw=None,
            tasks_raw=None,
        )

        assert "Charlie" in result
        assert "(none)" in result

    def test_empty_lists(self) -> None:
        workflow = CandidateSummaryWorkflow()
        result = workflow._build_input([], [], [])

        assert "(not available)" in result



