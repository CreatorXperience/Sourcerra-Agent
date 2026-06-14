import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.interview import InterviewQuestionAgent
from app.schemas.agents import AgentConfig, AgentRunResponse, AgentStatus, AgentType
from app.schemas.tools import ToolCallStatus, ToolResult
from app.schemas.workflows import InterviewQuestion, InterviewQuestionOutput
from app.workflows.interview_questions import InterviewQuestionWorkflow


@pytest.fixture(autouse=True)
def _mock_openai_client() -> None:
    with patch("app.agents.interview.AsyncOpenAI") as mock_client:
        mock_client.return_value = MagicMock()
        yield


@pytest.fixture
def agent() -> InterviewQuestionAgent:
    return InterviewQuestionAgent(
        AgentConfig(name="interview-question-generator", agent_type=AgentType.INTERVIEW_QUESTION),
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
    "stage": "SHORTLISTED",
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


class TestInterviewQuestionAgent:
    async def test_agent_registered(self) -> None:
        from app.agents import register_default_agents
        from app.agents.registry import AgentRegistry

        registry = AgentRegistry()
        register_default_agents(registry)
        registered = registry.get("interview-question-generator")

        assert registered is not None
        assert registered.config.name == "interview-question-generator"
        assert registered.config.agent_type == AgentType.INTERVIEW_QUESTION

    @patch("app.agents.interview.Runner.run")
    async def test_run_returns_structured_output(self, mock_run: MagicMock, agent: InterviewQuestionAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = InterviewQuestionOutput(
            candidate_id="cand-1",
            job_id="job-1",
            job_title="Senior Python Backend Engineer",
            technical_questions=[
                InterviewQuestion(
                    question="Describe your experience building distributed systems with Python",
                    type="technical",
                    focus_area="Backend architecture",
                    rationale="Candidate has strong backend skills; probes depth at scale",
                ),
            ],
            behavioral_questions=[
                InterviewQuestion(
                    question="Tell me about a time you disagreed with a technical decision",
                    type="behavioral",
                    focus_area="Communication",
                    rationale="Assesses collaboration style",
                ),
            ],
            follow_up_questions=[
                InterviewQuestion(
                    question="How would you approach learning Kubernetes on the job?",
                    type="follow_up",
                    focus_area="Growth mindset",
                    rationale="Candidate lacks K8s experience, which is required",
                ),
            ],
            focus_areas=["Backend architecture", "AWS infrastructure", "Problem-solving approach"],
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="some candidate and job data")

        assert result.status == AgentStatus.COMPLETED
        assert result.agent_name == "interview-question-generator"
        assert result.error is None
        assert "cand-1" in (result.output or "")

    @patch("app.agents.interview.Runner.run")
    async def test_run_includes_all_question_categories(self, mock_run: MagicMock, agent: InterviewQuestionAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = InterviewQuestionOutput(
            candidate_id="cand-2",
            job_id="job-2",
            job_title="DevOps Engineer",
            technical_questions=[
                InterviewQuestion(question="Q1", type="technical", focus_area="CI/CD", rationale="Assesses pipeline knowledge"),
            ],
            behavioral_questions=[
                InterviewQuestion(question="Q2", type="behavioral", focus_area="Teamwork", rationale="Assesses collaboration"),
            ],
            follow_up_questions=[
                InterviewQuestion(question="Q3", type="follow_up", focus_area="Learning", rationale="Probes gap"),
            ],
            focus_areas=["CI/CD", "Cloud infrastructure"],
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="data")
        output = json.loads(result.output or "{}")

        assert "technical_questions" in output
        assert "behavioral_questions" in output
        assert "follow_up_questions" in output
        assert "focus_areas" in output
        assert output["candidate_id"] == "cand-2"

    @patch("app.agents.interview.Runner.run")
    async def test_run_loads_prompt_template(self, mock_run: MagicMock, agent: InterviewQuestionAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = InterviewQuestionOutput(
            candidate_id="c-1", job_id="j-1", job_title="T",
            technical_questions=[], behavioral_questions=[], follow_up_questions=[],
            focus_areas=[],
        )
        mock_run.return_value = mock_result

        await agent.run(task="data")

        args, _ = mock_run.call_args
        openai_agent = args[0]
        instructions = openai_agent.instructions
        assert "Technical Questions" in instructions
        assert "Behavioral Questions" in instructions
        assert "Follow-up Questions" in instructions
        assert "focus_area" in instructions
        assert "rationale" in instructions


class TestInterviewQuestionWorkflow:
    async def test_missing_agent_returns_error(self) -> None:
        with patch("app.workflows.interview_questions.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = None
            mock_reg.return_value = mock_registry

            workflow = InterviewQuestionWorkflow()
            result = await workflow.execute(candidate_id="cand-1", job_id="job-1")

        assert result.status == AgentStatus.ERROR
        assert result.error and "not registered" in result.error

    async def test_missing_mcp_manager_returns_error(self) -> None:
        with patch("app.workflows.interview_questions.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = MagicMock()
            mock_reg.return_value = mock_registry

            workflow = InterviewQuestionWorkflow()
            result = await workflow.execute(candidate_id="cand-1", job_id="job-1", mcp_manager=None)

        assert result.status == AgentStatus.ERROR
        assert result.error and "not available" in result.error

    async def test_missing_candidate_returns_error(self) -> None:
        mock_agent = MagicMock()

        with patch("app.workflows.interview_questions.get_registry") as mock_reg:
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

            workflow = InterviewQuestionWorkflow()
            result = await workflow.execute(candidate_id="bad-cand", job_id="job-1", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.ERROR
        assert "not found" in (result.error or "")

    async def test_missing_job_returns_error(self) -> None:
        mock_agent = MagicMock()

        with patch("app.workflows.interview_questions.get_registry") as mock_reg:
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

            workflow = InterviewQuestionWorkflow()
            result = await workflow.execute(candidate_id="cand-1", job_id="bad-job", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.ERROR
        assert "not found" in (result.error or "")

    async def test_happy_path_all_data(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.run.return_value = AgentRunResponse(
            run_id="run-1",
            agent_name="interview-question-generator",
            status=AgentStatus.COMPLETED,
            output=json.dumps({
                "candidate_id": "cand-1",
                "job_id": "job-1",
                "job_title": "Senior Python Backend Engineer",
                "technical_questions": [{"question": "Q1", "type": "technical", "focus_area": "Backend", "rationale": "R1"}],
                "behavioral_questions": [],
                "follow_up_questions": [],
                "focus_areas": ["Backend"],
            }),
        )

        with patch("app.workflows.interview_questions.get_registry") as mock_reg:
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
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown")

            mock_mcp.call_tool = mock_call_tool

            workflow = InterviewQuestionWorkflow()
            result = await workflow.execute(candidate_id="cand-1", job_id="job-1", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.COMPLETED
        assert "cand-1" in (result.output or "")
        mock_agent.run.assert_called_once()

    async def test_works_without_comments(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.run.return_value = AgentRunResponse(
            run_id="run-2",
            agent_name="interview-question-generator",
            status=AgentStatus.COMPLETED,
            output=json.dumps({
                "candidate_id": "cand-1",
                "job_id": "job-1",
                "job_title": "Engineer",
                "technical_questions": [],
                "behavioral_questions": [],
                "follow_up_questions": [],
                "focus_areas": [],
            }),
        )

        with patch("app.workflows.interview_questions.get_registry") as mock_reg:
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
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown")

            mock_mcp.call_tool = mock_call_tool

            workflow = InterviewQuestionWorkflow()
            result = await workflow.execute(candidate_id="cand-1", job_id="job-1", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.COMPLETED


class TestBuildInput:
    def test_build_input_all_data(self) -> None:
        workflow = InterviewQuestionWorkflow()
        result = workflow._build_input(
            candidate_raw=[{"text": SAMPLE_CANDIDATE_TEXT}],
            job_raw=[{"text": SAMPLE_JOB_TEXT}],
            comments_raw=[{"text": SAMPLE_COMMENTS_TEXT}],
        )

        assert "CANDIDATE PROFILE" in result
        assert "JOB INFORMATION" in result
        assert "RECRUITER COMMENTS" in result
        assert "Alice Smith" in result
        assert "Senior Python Backend Engineer" in result
        assert "Excellent communication skills" in result

    def test_build_input_no_comments(self) -> None:
        workflow = InterviewQuestionWorkflow()
        result = workflow._build_input(
            candidate_raw=[{"text": SAMPLE_CANDIDATE_TEXT}],
            job_raw=[{"text": SAMPLE_JOB_TEXT}],
            comments_raw=None,
        )

        assert "CANDIDATE PROFILE" in result
        assert "JOB INFORMATION" in result
        assert "RECRUITER COMMENTS" in result
        assert "(none)" in result

    def test_build_input_empty_comments(self) -> None:
        workflow = InterviewQuestionWorkflow()
        result = workflow._build_input(
            candidate_raw=[{"text": SAMPLE_CANDIDATE_TEXT}],
            job_raw=[{"text": SAMPLE_JOB_TEXT}],
            comments_raw=[{"text": ""}],
        )

        assert "(none)" in result


class TestEndpoint:
    @patch("app.api.v1.ats.InterviewQuestionWorkflow")
    async def test_endpoint_returns_200(self, mock_workflow_cls: MagicMock, client) -> None:
        mock_workflow = AsyncMock()
        mock_workflow.execute.return_value = AgentRunResponse(
            run_id="run-1",
            agent_name="interview-question-generator",
            status=AgentStatus.COMPLETED,
            output=json.dumps({
                "candidate_id": "cand-1",
                "job_id": "job-1",
                "job_title": "Senior Python Backend Engineer",
                "technical_questions": [
                    {"question": "Describe your experience with Python async", "type": "technical", "focus_area": "Python", "rationale": "Assesses depth in Python"},
                ],
                "behavioral_questions": [],
                "follow_up_questions": [],
                "focus_areas": ["Python", "System design"],
            }),
        )
        mock_workflow_cls.return_value = mock_workflow

        response = await client.post(
            "/api/v1/generate-interview-questions",
            json={"candidate_id": "cand-123", "job_id": "job-456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    async def test_endpoint_missing_job_id(self, client) -> None:
        response = await client.post(
            "/api/v1/generate-interview-questions",
            json={"candidate_id": "cand-123"},
        )
        assert response.status_code == 422

    async def test_endpoint_missing_candidate_id(self, client) -> None:
        response = await client.post(
            "/api/v1/generate-interview-questions",
            json={"job_id": "job-456"},
        )
        assert response.status_code == 422
