import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.hiring_recommendation import HiringRecommendationAgent
from app.schemas.agents import AgentConfig, AgentRunResponse, AgentStatus, AgentType
from app.schemas.tools import ToolCallStatus, ToolResult
from app.schemas.workflows import HiringRecommendationOutput
from app.workflows.hiring_recommendation import HiringRecommendationWorkflow


@pytest.fixture(autouse=True)
def _mock_openai_client() -> None:
    with patch("app.agents.hiring_recommendation.AsyncOpenAI") as mock_client:
        mock_client.return_value = MagicMock()
        yield


@pytest.fixture
def agent() -> HiringRecommendationAgent:
    return HiringRecommendationAgent(
        AgentConfig(name="hiring-recommendation", agent_type=AgentType.GENERAL),
    )


SAMPLE_CANDIDATE_TEXT = json.dumps({
    "id": "cand-1",
    "name": "Alice Smith",
    "email": "alice@example.com",
    "skills": ["Python", "AWS", "Docker", "PostgreSQL", "FastAPI"],
    "seniority": "Senior",
    "last_role": "Senior Backend Engineer at TechCorp",
    "years_of_experience": 8,
    "location": "San Francisco, CA",
    "overall_score": 92.0,
    "skills_score": 90.0,
    "experience_score": 88.0,
    "strengths": ["Strong backend architecture skills", "Excellent problem solver"],
    "weaknesses": ["No Kubernetes experience", "Limited frontend exposure"],
    "stage": "INTERVIEW",
})

SAMPLE_COMMENTS_TEXT = json.dumps([
    {"id": "c1", "candidate_id": "cand-1", "content": "Excellent communication skills"},
    {"id": "c2", "candidate_id": "cand-1", "content": "Strong technical background"},
])

SAMPLE_TASKS_TEXT = json.dumps([
    {"id": "t1", "candidate_id": "cand-1", "description": "Schedule technical interview", "status": "completed"},
    {"id": "t2", "candidate_id": "cand-1", "description": "Collect references", "status": "pending"},
])

SAMPLE_TIMELINE_TEXT = json.dumps([
    {"event": "Applied", "date": "2026-05-01"},
    {"event": "Screened", "date": "2026-05-05"},
    {"event": "Technical Interview", "date": "2026-05-12"},
])

SAMPLE_COMMUNICATION_TEXT = json.dumps([
    {"type": "email", "subject": "Interview invitation", "sent_at": "2026-05-03"},
    {"type": "email", "subject": "Follow-up", "sent_at": "2026-05-10"},
])

SAMPLE_INTERVIEWS_TEXT = json.dumps([
    {"id": "int-1", "type": "technical", "status": "completed", "score": 4.5},
    {"id": "int-2", "type": "behavioral", "status": "completed", "score": 4.0},
])

SAMPLE_SIGNALS_TEXT = json.dumps([
    {"type": "skill_assessment", "result": "pass", "label": "Python Advanced"},
    {"type": "coding_challenge", "result": "strong", "label": "Algorithmic thinking"},
])


class TestHiringRecommendationAgent:
    async def test_agent_registered(self) -> None:
        from app.agents import register_default_agents
        from app.agents.registry import AgentRegistry

        registry = AgentRegistry()
        register_default_agents(registry)
        registered = registry.get("hiring-recommendation")

        assert registered is not None
        assert registered.config.name == "hiring-recommendation"

    @patch("app.agents.hiring_recommendation.Runner.run")
    async def test_run_returns_structured_output(self, mock_run: MagicMock, agent: HiringRecommendationAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = HiringRecommendationOutput(
            candidate_id="cand-1",
            candidate_name="Alice Smith",
            candidate_summary="Alice is a Senior Backend Engineer with strong Python skills.",
            supporting_evidence=["Technical interview score of 4.5/5 confirms depth"],
            caution_evidence=["No Kubernetes experience noted in profile"],
            risk_factors=["Missing required K8s skill for the role"],
            missing_information=["Reference checks not yet completed"],
            recruiter_recommendation="Advance with Caution",
            confidence_level="High",
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="some candidate data")

        assert result.status == AgentStatus.COMPLETED
        assert result.agent_name == "hiring-recommendation"
        assert result.error is None
        assert "cand-1" in (result.output or "")

    @patch("app.agents.hiring_recommendation.Runner.run")
    async def test_run_includes_all_output_fields(self, mock_run: MagicMock, agent: HiringRecommendationAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = HiringRecommendationOutput(
            candidate_id="cand-2",
            candidate_name="Bob Jones",
            candidate_summary="Summary",
            supporting_evidence=["E1", "E2"],
            caution_evidence=["C1"],
            risk_factors=["R1", "R2"],
            missing_information=["M1"],
            recruiter_recommendation="Hold for More Information",
            confidence_level="Moderate",
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="data")
        output = json.loads(result.output or "{}")

        assert "candidate_summary" in output
        assert "supporting_evidence" in output
        assert "caution_evidence" in output
        assert "risk_factors" in output
        assert "missing_information" in output
        assert "recruiter_recommendation" in output
        assert "confidence_level" in output
        assert output["candidate_id"] == "cand-2"
        assert output["candidate_name"] == "Bob Jones"

    @patch("app.agents.hiring_recommendation.Runner.run")
    async def test_run_loads_prompt_template(self, mock_run: MagicMock, agent: HiringRecommendationAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = HiringRecommendationOutput(
            candidate_id="c-1", candidate_name="N",
            candidate_summary="S", supporting_evidence=[], caution_evidence=[],
            risk_factors=[], missing_information=[],
            recruiter_recommendation="Do Not Advance",
            confidence_level="Low",
        )
        mock_run.return_value = mock_result

        await agent.run(task="data")

        args, _ = mock_run.call_args
        openai_agent = args[0]
        instructions = openai_agent.instructions
        assert "Evidence Supporting Advancement" in instructions
        assert "Evidence Supporting Caution" in instructions
        assert "Risk Factors" in instructions
        assert "Missing Information" in instructions
        assert "Recruiter Recommendation" in instructions
        assert "Confidence Level" in instructions


class TestHiringRecommendationWorkflow:
    async def test_missing_agent_returns_error(self) -> None:
        with patch("app.workflows.hiring_recommendation.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = None
            mock_reg.return_value = mock_registry

            workflow = HiringRecommendationWorkflow()
            result = await workflow.execute(candidate_id="cand-1")

        assert result.status == AgentStatus.ERROR
        assert result.error and "not registered" in result.error

    async def test_missing_mcp_manager_returns_error(self) -> None:
        with patch("app.workflows.hiring_recommendation.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = MagicMock()
            mock_reg.return_value = mock_registry

            workflow = HiringRecommendationWorkflow()
            result = await workflow.execute(candidate_id="cand-1", mcp_manager=None)

        assert result.status == AgentStatus.ERROR
        assert result.error and "not available" in result.error

    async def test_missing_candidate_returns_error(self) -> None:
        mock_agent = MagicMock()

        with patch("app.workflows.hiring_recommendation.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_agent
            mock_reg.return_value = mock_registry

            mock_mcp = AsyncMock()

            async def mock_call_tool(name: str, args: dict) -> ToolResult:
                if name == "ats_get_candidate":
                    return ToolResult(status=ToolCallStatus.ERROR, error="Candidate not found")
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown")

            mock_mcp.call_tool = mock_call_tool

            workflow = HiringRecommendationWorkflow()
            result = await workflow.execute(candidate_id="bad-cand", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.ERROR
        assert "not found" in (result.error or "")

    async def test_happy_path_all_data(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.run.return_value = AgentRunResponse(
            run_id="run-1",
            agent_name="hiring-recommendation",
            status=AgentStatus.COMPLETED,
            output=json.dumps({
                "candidate_id": "cand-1",
                "candidate_name": "Alice Smith",
                "candidate_summary": "Strong backend candidate.",
                "supporting_evidence": ["4.5 technical score"],
                "caution_evidence": ["K8s gap"],
                "risk_factors": ["Missing required skill"],
                "missing_information": ["References pending"],
                "recruiter_recommendation": "Advance with Caution",
                "confidence_level": "High",
            }),
        )

        with patch("app.workflows.hiring_recommendation.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_agent
            mock_reg.return_value = mock_registry

            mock_mcp = AsyncMock()

            async def mock_call_tool(name: str, args: dict) -> ToolResult:
                if name == "ats_get_candidate":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_CANDIDATE_TEXT}])
                if name == "ats_get_candidate_comments":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_COMMENTS_TEXT}])
                if name == "ats_get_candidate_tasks":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_TASKS_TEXT}])
                if name == "ats_get_candidate_timeline":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_TIMELINE_TEXT}])
                if name == "ats_get_candidate_communication":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_COMMUNICATION_TEXT}])
                if name == "ats_get_candidate_interviews":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_INTERVIEWS_TEXT}])
                if name == "ats_get_candidate_signals":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_SIGNALS_TEXT}])
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown")

            mock_mcp.call_tool = mock_call_tool

            workflow = HiringRecommendationWorkflow()
            result = await workflow.execute(candidate_id="cand-1", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.COMPLETED
        assert "cand-1" in (result.output or "")
        assert "Advance with Caution" in (result.output or "")
        mock_agent.run.assert_called_once()

    async def test_works_without_optional_data(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.run.return_value = AgentRunResponse(
            run_id="run-2",
            agent_name="hiring-recommendation",
            status=AgentStatus.COMPLETED,
            output=json.dumps({
                "candidate_id": "cand-1",
                "candidate_name": "Alice Smith",
                "candidate_summary": "Limited data available.",
                "supporting_evidence": [],
                "caution_evidence": [],
                "risk_factors": [],
                "missing_information": ["All optional data sources missing"],
                "recruiter_recommendation": "Hold for More Information",
                "confidence_level": "Low",
            }),
        )

        with patch("app.workflows.hiring_recommendation.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_agent
            mock_reg.return_value = mock_registry

            mock_mcp = AsyncMock()

            async def mock_call_tool(name: str, args: dict) -> ToolResult:
                if name == "ats_get_candidate":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_CANDIDATE_TEXT}])
                if name == "ats_get_candidate_comments":
                    return ToolResult(status=ToolCallStatus.ERROR, error="No comments")
                if name == "ats_get_candidate_tasks":
                    return ToolResult(status=ToolCallStatus.ERROR, error="No tasks")
                if name == "ats_get_candidate_timeline":
                    return ToolResult(status=ToolCallStatus.ERROR, error="No timeline")
                if name == "ats_get_candidate_communication":
                    return ToolResult(status=ToolCallStatus.ERROR, error="No communication")
                if name == "ats_get_candidate_interviews":
                    return ToolResult(status=ToolCallStatus.ERROR, error="No interviews")
                if name == "ats_get_candidate_signals":
                    return ToolResult(status=ToolCallStatus.ERROR, error="No signals")
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown")

            mock_mcp.call_tool = mock_call_tool

            workflow = HiringRecommendationWorkflow()
            result = await workflow.execute(candidate_id="cand-1", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.COMPLETED


class TestBuildInput:
    def test_build_input_all_data(self) -> None:
        workflow = HiringRecommendationWorkflow()
        result = workflow._build_input(
            candidate_raw=[{"text": SAMPLE_CANDIDATE_TEXT}],
            comments_raw=[{"text": SAMPLE_COMMENTS_TEXT}],
            tasks_raw=[{"text": SAMPLE_TASKS_TEXT}],
            timeline_raw=[{"text": SAMPLE_TIMELINE_TEXT}],
            communication_raw=[{"text": SAMPLE_COMMUNICATION_TEXT}],
            interviews_raw=[{"text": SAMPLE_INTERVIEWS_TEXT}],
            signals_raw=[{"text": SAMPLE_SIGNALS_TEXT}],
        )

        assert "CANDIDATE PROFILE" in result
        assert "RECRUITER COMMENTS" in result
        assert "CANDIDATE TASKS" in result
        assert "CANDIDATE TIMELINE" in result
        assert "CANDIDATE COMMUNICATION" in result
        assert "CANDIDATE INTERVIEWS" in result
        assert "CANDIDATE SIGNALS" in result
        assert "Alice Smith" in result

    def test_build_input_no_optional_data(self) -> None:
        workflow = HiringRecommendationWorkflow()
        result = workflow._build_input(
            candidate_raw=[{"text": SAMPLE_CANDIDATE_TEXT}],
            comments_raw=None,
            tasks_raw=None,
            timeline_raw=None,
            communication_raw=None,
            interviews_raw=None,
            signals_raw=None,
        )

        assert "CANDIDATE PROFILE" in result
        assert "(none)" in result

    def test_build_input_empty_optional_data(self) -> None:
        workflow = HiringRecommendationWorkflow()
        result = workflow._build_input(
            candidate_raw=[{"text": SAMPLE_CANDIDATE_TEXT}],
            comments_raw=[{"text": ""}],
            tasks_raw=[{"text": ""}],
            timeline_raw=[{"text": ""}],
            communication_raw=[{"text": ""}],
            interviews_raw=[{"text": ""}],
            signals_raw=[{"text": ""}],
        )

        assert "(none)" in result


class TestEndpoint:
    @patch("app.api.v1.ats.HiringRecommendationWorkflow")
    async def test_endpoint_returns_200(self, mock_workflow_cls: MagicMock, client) -> None:
        mock_workflow = AsyncMock()
        mock_workflow.execute.return_value = AgentRunResponse(
            run_id="run-1",
            agent_name="hiring-recommendation",
            status=AgentStatus.COMPLETED,
            output=json.dumps({
                "candidate_id": "cand-1",
                "candidate_name": "Alice Smith",
                "candidate_summary": "Alice is a strong backend candidate.",
                "supporting_evidence": ["Technical score 4.5"],
                "caution_evidence": [],
                "risk_factors": [],
                "missing_information": [],
                "recruiter_recommendation": "Strong Advance",
                "confidence_level": "High",
            }),
        )
        mock_workflow_cls.return_value = mock_workflow

        response = await client.post(
            "/api/v1/hiring-recommendation",
            json={"candidate_id": "cand-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    async def test_endpoint_missing_candidate_id(self, client) -> None:
        response = await client.post(
            "/api/v1/hiring-recommendation",
            json={},
        )
        assert response.status_code == 422

    async def test_endpoint_empty_body(self, client) -> None:
        response = await client.post(
            "/api/v1/hiring-recommendation",
            json={},
        )
        assert response.status_code == 422
