import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.interview_debrief import InterviewDebriefAgent
from app.schemas.agents import AgentConfig, AgentRunResponse, AgentStatus, AgentType
from app.schemas.tools import ToolCallStatus, ToolResult
from app.schemas.workflows import InterviewDebriefOutput
from app.workflows.interview_debrief import InterviewDebriefWorkflow


@pytest.fixture(autouse=True)
def _mock_openai_client() -> None:
    with patch("app.agents.interview_debrief.AsyncOpenAI") as mock_client:
        mock_client.return_value = MagicMock()
        yield


@pytest.fixture
def agent() -> InterviewDebriefAgent:
    return InterviewDebriefAgent(
        AgentConfig(name="interview-debrief", agent_type=AgentType.GENERAL),
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

SAMPLE_JOB_TEXT = json.dumps({
    "id": "job-1",
    "title": "Senior Python Backend Engineer",
    "description": "Build and maintain distributed backend services",
    "requirements": [
        {"label": "Python", "field_type": "skill", "required": True},
        {"label": "AWS", "field_type": "skill", "required": True},
        {"label": "Docker", "field_type": "skill", "required": False},
        {"label": "Kubernetes", "field_type": "skill", "required": True},
    ],
})

SAMPLE_COMMENTS_TEXT = json.dumps([
    {"id": "c1", "candidate_id": "cand-1", "content": "Excellent communication skills"},
    {"id": "c2", "candidate_id": "cand-1", "content": "Strong technical background"},
])

SAMPLE_INTERVIEWS_TEXT = json.dumps([
    {"id": "int-1", "candidate_id": "cand-1", "job_id": "job-1", "type": "technical", "status": "completed", "score": 4.5},
    {"id": "int-2", "candidate_id": "cand-1", "job_id": "job-1", "type": "behavioral", "status": "completed", "score": 4.0},
])

SAMPLE_FEEDBACK_TEXT = json.dumps({
    "interview_id": "int-1",
    "ratings": {"technical_skill": 5, "problem_solving": 4, "communication": 5},
    "strengths": ["Deep Python knowledge", "Excellent system design"],
    "concerns": ["Limited Kubernetes exposure"],
    "notes": "Strong candidate, recommend moving forward",
})

SAMPLE_SIGNALS_TEXT = json.dumps({
    "candidate_id": "cand-1",
    "signals": [
        {"type": "skill_assessment", "result": "pass", "label": "Python Advanced"},
        {"type": "coding_challenge", "result": "strong", "label": "Algorithmic thinking"},
    ],
})


class TestInterviewDebriefAgent:
    async def test_agent_registered(self) -> None:
        from app.agents import register_default_agents
        from app.agents.registry import AgentRegistry

        registry = AgentRegistry()
        register_default_agents(registry)
        registered = registry.get("interview-debrief")

        assert registered is not None
        assert registered.config.name == "interview-debrief"

    @patch("app.agents.interview_debrief.Runner.run")
    async def test_run_returns_structured_output(self, mock_run: MagicMock, agent: InterviewDebriefAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = InterviewDebriefOutput(
            candidate_id="cand-1",
            job_id="job-1",
            interview_summary="Alice Smith completed two interview rounds. Technical skills were strong across the board.",
            validated_strengths=["Deep Python knowledge validated during technical interview"],
            identified_concerns=["Limited Kubernetes exposure noted in technical interview"],
            further_evaluation_areas=["System design at scale - not fully assessed"],
            overall_assessment="Alice is a strong backend candidate with minor gaps in Kubernetes.",
            recommended_next_step="Move to Final Interview",
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="some candidate and interview data")

        assert result.status == AgentStatus.COMPLETED
        assert result.agent_name == "interview-debrief"
        assert result.error is None
        assert "cand-1" in (result.output or "")

    @patch("app.agents.interview_debrief.Runner.run")
    async def test_run_includes_all_output_fields(self, mock_run: MagicMock, agent: InterviewDebriefAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = InterviewDebriefOutput(
            candidate_id="cand-2",
            job_id="job-2",
            interview_summary="Summary text here",
            validated_strengths=["Strength A", "Strength B"],
            identified_concerns=["Concern A"],
            further_evaluation_areas=["Area A", "Area B"],
            overall_assessment="Assessment text",
            recommended_next_step="Schedule Follow-up Interview",
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="data")
        output = json.loads(result.output or "{}")

        assert "interview_summary" in output
        assert "validated_strengths" in output
        assert "identified_concerns" in output
        assert "further_evaluation_areas" in output
        assert "overall_assessment" in output
        assert "recommended_next_step" in output
        assert output["candidate_id"] == "cand-2"
        assert output["job_id"] == "job-2"

    @patch("app.agents.interview_debrief.Runner.run")
    async def test_run_loads_prompt_template(self, mock_run: MagicMock, agent: InterviewDebriefAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = InterviewDebriefOutput(
            candidate_id="c-1", job_id="j-1",
            interview_summary="S", validated_strengths=[], identified_concerns=[],
            further_evaluation_areas=[], overall_assessment="A",
            recommended_next_step="Hold for Review",
        )
        mock_run.return_value = mock_result

        await agent.run(task="data")

        args, _ = mock_run.call_args
        openai_agent = args[0]
        instructions = openai_agent.instructions
        assert "Interview Summary" in instructions
        assert "Validated Strengths" in instructions
        assert "Identified Concerns" in instructions
        assert "Areas Requiring Further Evaluation" in instructions
        assert "Overall Assessment" in instructions
        assert "Recommended Next Step" in instructions


class TestInterviewDebriefWorkflow:
    async def test_missing_agent_returns_error(self) -> None:
        with patch("app.workflows.interview_debrief.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = None
            mock_reg.return_value = mock_registry

            workflow = InterviewDebriefWorkflow()
            result = await workflow.execute(candidate_id="cand-1", job_id="job-1")

        assert result.status == AgentStatus.ERROR
        assert result.error and "not registered" in result.error

    async def test_missing_mcp_manager_returns_error(self) -> None:
        with patch("app.workflows.interview_debrief.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = MagicMock()
            mock_reg.return_value = mock_registry

            workflow = InterviewDebriefWorkflow()
            result = await workflow.execute(candidate_id="cand-1", job_id="job-1", mcp_manager=None)

        assert result.status == AgentStatus.ERROR
        assert result.error and "not available" in result.error

    async def test_missing_candidate_returns_error(self) -> None:
        mock_agent = MagicMock()

        with patch("app.workflows.interview_debrief.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_agent
            mock_reg.return_value = mock_registry

            mock_mcp = AsyncMock()

            async def mock_call_tool(name: str, args: dict) -> ToolResult:
                if name == "ats_get_candidate":
                    return ToolResult(status=ToolCallStatus.ERROR, error="Candidate not found")
                if name == "ats_get_job":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_JOB_TEXT}])
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown")

            mock_mcp.call_tool = mock_call_tool

            workflow = InterviewDebriefWorkflow()
            result = await workflow.execute(candidate_id="bad-cand", job_id="job-1", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.ERROR
        assert "not found" in (result.error or "")

    async def test_missing_job_returns_error(self) -> None:
        mock_agent = MagicMock()

        with patch("app.workflows.interview_debrief.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_agent
            mock_reg.return_value = mock_registry

            mock_mcp = AsyncMock()

            async def mock_call_tool(name: str, args: dict) -> ToolResult:
                if name == "ats_get_candidate":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_CANDIDATE_TEXT}])
                if name == "ats_get_job":
                    return ToolResult(status=ToolCallStatus.ERROR, error="Job not found")
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown")

            mock_mcp.call_tool = mock_call_tool

            workflow = InterviewDebriefWorkflow()
            result = await workflow.execute(candidate_id="cand-1", job_id="bad-job", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.ERROR
        assert "not found" in (result.error or "")

    async def test_happy_path_all_data(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.run.return_value = AgentRunResponse(
            run_id="run-1",
            agent_name="interview-debrief",
            status=AgentStatus.COMPLETED,
            output=json.dumps({
                "candidate_id": "cand-1",
                "job_id": "job-1",
                "interview_summary": "Alice completed two interviews with strong results.",
                "validated_strengths": ["Python", "System design"],
                "identified_concerns": ["Kubernetes gap"],
                "further_evaluation_areas": ["System design at scale"],
                "overall_assessment": "Strong backend candidate.",
                "recommended_next_step": "Move to Final Interview",
            }),
        )

        with patch("app.workflows.interview_debrief.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_agent
            mock_reg.return_value = mock_registry

            mock_mcp = AsyncMock()

            async def mock_call_tool(name: str, args: dict) -> ToolResult:
                if name == "ats_get_candidate":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_CANDIDATE_TEXT}])
                if name == "ats_get_job":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_JOB_TEXT}])
                if name == "ats_get_candidate_comments":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_COMMENTS_TEXT}])
                if name == "ats_get_candidate_interviews":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_INTERVIEWS_TEXT}])
                if name == "ats_get_interview_feedback":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_FEEDBACK_TEXT}])
                if name == "ats_get_candidate_signals":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_SIGNALS_TEXT}])
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown")

            mock_mcp.call_tool = mock_call_tool

            workflow = InterviewDebriefWorkflow()
            result = await workflow.execute(candidate_id="cand-1", job_id="job-1", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.COMPLETED
        assert "cand-1" in (result.output or "")
        assert "Move to Final Interview" in (result.output or "")
        mock_agent.run.assert_called_once()

    async def test_works_without_optional_data(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.run.return_value = AgentRunResponse(
            run_id="run-2",
            agent_name="interview-debrief",
            status=AgentStatus.COMPLETED,
            output=json.dumps({
                "candidate_id": "cand-1",
                "job_id": "job-1",
                "interview_summary": "Limited interview data available.",
                "validated_strengths": [],
                "identified_concerns": [],
                "further_evaluation_areas": ["Complete interview process required"],
                "overall_assessment": "Insufficient data for full assessment.",
                "recommended_next_step": "Gather Additional Feedback",
            }),
        )

        with patch("app.workflows.interview_debrief.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_agent
            mock_reg.return_value = mock_registry

            mock_mcp = AsyncMock()

            async def mock_call_tool(name: str, args: dict) -> ToolResult:
                if name == "ats_get_candidate":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_CANDIDATE_TEXT}])
                if name == "ats_get_job":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_JOB_TEXT}])
                if name == "ats_get_candidate_comments":
                    return ToolResult(status=ToolCallStatus.ERROR, error="No comments")
                if name == "ats_get_candidate_interviews":
                    return ToolResult(status=ToolCallStatus.ERROR, error="No interviews")
                if name == "ats_get_candidate_signals":
                    return ToolResult(status=ToolCallStatus.ERROR, error="No signals")
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown")

            mock_mcp.call_tool = mock_call_tool

            workflow = InterviewDebriefWorkflow()
            result = await workflow.execute(candidate_id="cand-1", job_id="job-1", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.COMPLETED


class TestBuildInput:
    def test_build_input_all_data(self) -> None:
        workflow = InterviewDebriefWorkflow()
        result = workflow._build_input(
            candidate_raw=[{"text": SAMPLE_CANDIDATE_TEXT}],
            job_raw=[{"text": SAMPLE_JOB_TEXT}],
            comments_raw=[{"text": SAMPLE_COMMENTS_TEXT}],
            interviews_raw=[{"text": SAMPLE_INTERVIEWS_TEXT}],
            feedbacks_raw=[{"interview_id": "int-1", "feedback": [{"text": SAMPLE_FEEDBACK_TEXT}]}],
            signals_raw=[{"text": SAMPLE_SIGNALS_TEXT}],
        )

        assert "CANDIDATE PROFILE" in result
        assert "JOB INFORMATION" in result
        assert "RECRUITER COMMENTS" in result
        assert "INTERVIEW RECORDS" in result
        assert "INTERVIEW FEEDBACK" in result
        assert "CANDIDATE SIGNALS" in result
        assert "Alice Smith" in result
        assert "Senior Python Backend Engineer" in result

    def test_build_input_no_optional_data(self) -> None:
        workflow = InterviewDebriefWorkflow()
        result = workflow._build_input(
            candidate_raw=[{"text": SAMPLE_CANDIDATE_TEXT}],
            job_raw=[{"text": SAMPLE_JOB_TEXT}],
            comments_raw=None,
            interviews_raw=None,
            feedbacks_raw=None,
            signals_raw=None,
        )

        assert "CANDIDATE PROFILE" in result
        assert "JOB INFORMATION" in result
        assert "RECRUITER COMMENTS" in result
        assert "INTERVIEW RECORDS" in result
        assert "INTERVIEW FEEDBACK" in result
        assert "CANDIDATE SIGNALS" in result
        assert "(none)" in result

    def test_build_input_empty_optional_data(self) -> None:
        workflow = InterviewDebriefWorkflow()
        result = workflow._build_input(
            candidate_raw=[{"text": SAMPLE_CANDIDATE_TEXT}],
            job_raw=[{"text": SAMPLE_JOB_TEXT}],
            comments_raw=[{"text": ""}],
            interviews_raw=[{"text": ""}],
            feedbacks_raw=[],
            signals_raw=[{"text": ""}],
        )

        assert "(none)" in result


class TestExtractInterviewIds:
    def test_extract_ids_from_list(self) -> None:
        workflow = InterviewDebriefWorkflow()
        ids = workflow._extract_interview_ids([{"text": SAMPLE_INTERVIEWS_TEXT}])
        assert ids == ["int-1", "int-2"]

    def test_extract_ids_from_single_dict(self) -> None:
        single_interview = json.dumps({"id": "int-1", "type": "technical"})
        workflow = InterviewDebriefWorkflow()
        ids = workflow._extract_interview_ids([{"text": single_interview}])
        assert ids == ["int-1"]

    def test_extract_ids_empty(self) -> None:
        workflow = InterviewDebriefWorkflow()
        ids = workflow._extract_interview_ids([{"text": ""}])
        assert ids == []

    def test_extract_ids_invalid_json(self) -> None:
        workflow = InterviewDebriefWorkflow()
        ids = workflow._extract_interview_ids([{"text": "not-json"}])
        assert ids == []


class TestEndpoint:
    @patch("app.api.v1.ats.InterviewDebriefWorkflow")
    async def test_endpoint_returns_200(self, mock_workflow_cls: MagicMock, client) -> None:
        mock_workflow = AsyncMock()
        mock_workflow.execute.return_value = AgentRunResponse(
            run_id="run-1",
            agent_name="interview-debrief",
            status=AgentStatus.COMPLETED,
            output=json.dumps({
                "candidate_id": "cand-1",
                "job_id": "job-1",
                "interview_summary": "Alice performed well across all interview rounds.",
                "validated_strengths": ["Technical depth", "Communication"],
                "identified_concerns": [],
                "further_evaluation_areas": ["Leadership experience"],
                "overall_assessment": "Strong candidate ready for final interview.",
                "recommended_next_step": "Move to Final Interview",
            }),
        )
        mock_workflow_cls.return_value = mock_workflow

        response = await client.post(
            "/api/v1/interview-debrief",
            json={"candidate_id": "cand-123", "job_id": "job-456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    async def test_endpoint_missing_job_id(self, client) -> None:
        response = await client.post(
            "/api/v1/interview-debrief",
            json={"candidate_id": "cand-123"},
        )
        assert response.status_code == 422

    async def test_endpoint_missing_candidate_id(self, client) -> None:
        response = await client.post(
            "/api/v1/interview-debrief",
            json={"job_id": "job-456"},
        )
        assert response.status_code == 422
