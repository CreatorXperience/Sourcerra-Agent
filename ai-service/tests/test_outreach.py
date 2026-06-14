import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.outreach import OutreachGenerationAgent
from app.schemas.agents import AgentConfig, AgentRunResponse, AgentStatus, AgentType
from app.schemas.tools import ToolCallStatus, ToolResult
from app.schemas.workflows import OutreachGenerationOutput
from app.workflows.outreach import OutreachGenerationWorkflow


@pytest.fixture(autouse=True)
def _mock_openai_client() -> None:
    with patch("app.agents.outreach.AsyncOpenAI") as mock_client:
        mock_client.return_value = MagicMock()
        yield


@pytest.fixture
def agent() -> OutreachGenerationAgent:
    return OutreachGenerationAgent(
        AgentConfig(name="outreach-specialist", agent_type=AgentType.OUTREACH),
    )


SAMPLE_CANDIDATE_TEXT = json.dumps({
    "id": "cand-1",
    "name": "Alice Smith",
    "email": "alice@example.com",
    "skills": ["Python", "AWS", "Docker", "PostgreSQL"],
    "seniority": "Senior",
    "last_role": "Senior Backend Engineer at TechCorp",
    "years_of_experience": 8,
    "location": "San Francisco, CA",
    "overall_score": 92.0,
    "strengths": ["Strong backend architecture skills", "Excellent problem solver"],
    "weaknesses": ["No Kubernetes experience"],
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
    ],
})

SAMPLE_COMMENTS_TEXT = json.dumps([
    {"id": "c1", "candidate_id": "cand-1", "content": "Excellent communication skills"},
    {"id": "c2", "candidate_id": "cand-1", "content": "Strong technical background"},
])


class TestOutreachGenerationAgent:
    async def test_agent_registered(self) -> None:
        from app.agents import register_default_agents
        from app.agents.registry import AgentRegistry

        registry = AgentRegistry()
        register_default_agents(registry)
        registered = registry.get("outreach-specialist")

        assert registered is not None
        assert registered.config.name == "outreach-specialist"
        assert registered.config.agent_type == AgentType.OUTREACH

    @patch("app.agents.outreach.Runner.run")
    async def test_run_returns_structured_output(self, mock_run: MagicMock, agent: OutreachGenerationAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = OutreachGenerationOutput(
            candidate_id="cand-1",
            job_id="job-1",
            candidate_name="Alice Smith",
            job_title="Senior Python Backend Engineer",
            subject="Exciting Opportunity: Senior Python Backend Engineer",
            email_body="Dear Alice,\n\nI came across your profile and was impressed...",
            linkedin_message="Hi Alice, I'm reaching out about a Senior Python Backend Engineer role...",
            short_message="Hi Alice, would you be open to chatting about a Senior Python role?",
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="some candidate and job data")

        assert result.status == AgentStatus.COMPLETED
        assert result.agent_name == "outreach-specialist"
        assert result.error is None
        assert "Alice Smith" in (result.output or "")
        assert "cand-1" in (result.output or "")

    @patch("app.agents.outreach.Runner.run")
    async def test_run_includes_all_message_formats(self, mock_run: MagicMock, agent: OutreachGenerationAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = OutreachGenerationOutput(
            candidate_id="cand-2",
            job_id="job-2",
            candidate_name="Bob Jones",
            job_title="DevOps Engineer",
            subject="DevOps Role at Sourcerra",
            email_body="Full email body here",
            linkedin_message="LinkedIn message here",
            short_message="Short text here",
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="data")
        output = json.loads(result.output or "{}")

        assert "subject" in output
        assert "email_body" in output
        assert "linkedin_message" in output
        assert "short_message" in output
        assert output["candidate_name"] == "Bob Jones"
        assert output["job_title"] == "DevOps Engineer"

    @patch("app.agents.outreach.Runner.run")
    async def test_run_loads_prompt_template(self, mock_run: MagicMock, agent: OutreachGenerationAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = OutreachGenerationOutput(
            candidate_id="c-1", job_id="j-1", candidate_name="Test", job_title="T",
            subject="S", email_body="E", linkedin_message="L", short_message="S",
        )
        mock_run.return_value = mock_result

        await agent.run(task="data")

        args, _ = mock_run.call_args
        openai_agent = args[0]
        instructions = openai_agent.instructions
        assert "Subject" in instructions
        assert "Email Body" in instructions
        assert "LinkedIn Message" in instructions
        assert "Short Message" in instructions


class TestOutreachGenerationWorkflow:
    async def test_missing_agent_returns_error(self) -> None:
        with patch("app.workflows.outreach.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = None
            mock_reg.return_value = mock_registry

            workflow = OutreachGenerationWorkflow()
            result = await workflow.execute(candidate_id="cand-1", job_id="job-1")

        assert result.status == AgentStatus.ERROR
        assert result.error and "not registered" in result.error

    async def test_missing_mcp_manager_returns_error(self) -> None:
        with patch("app.workflows.outreach.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = MagicMock()
            mock_reg.return_value = mock_registry

            workflow = OutreachGenerationWorkflow()
            result = await workflow.execute(candidate_id="cand-1", job_id="job-1", mcp_manager=None)

        assert result.status == AgentStatus.ERROR
        assert result.error and "not available" in result.error

    async def test_missing_candidate_returns_error(self) -> None:
        mock_agent = MagicMock()

        with patch("app.workflows.outreach.get_registry") as mock_reg:
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

            workflow = OutreachGenerationWorkflow()
            result = await workflow.execute(candidate_id="bad-cand", job_id="job-1", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.ERROR
        assert "not found" in (result.error or "")

    async def test_missing_job_returns_error(self) -> None:
        mock_agent = MagicMock()

        with patch("app.workflows.outreach.get_registry") as mock_reg:
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

            workflow = OutreachGenerationWorkflow()
            result = await workflow.execute(candidate_id="cand-1", job_id="bad-job", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.ERROR
        assert "not found" in (result.error or "")

    async def test_happy_path_all_data(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.run.return_value = AgentRunResponse(
            run_id="run-1",
            agent_name="outreach-specialist",
            status=AgentStatus.COMPLETED,
            output='{"candidate_id":"cand-1","job_id":"job-1","candidate_name":"Alice Smith","job_title":"Senior Python Backend Engineer","subject":"Exciting Opportunity","email_body":"Dear Alice...","linkedin_message":"Hi Alice...","short_message":"Hi Alice, interested?"}',
        )

        with patch("app.workflows.outreach.get_registry") as mock_reg:
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

            workflow = OutreachGenerationWorkflow()
            result = await workflow.execute(candidate_id="cand-1", job_id="job-1", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.COMPLETED
        assert "Alice" in (result.output or "")
        mock_agent.run.assert_called_once()

    async def test_works_without_comments(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.run.return_value = AgentRunResponse(
            run_id="run-2",
            agent_name="outreach-specialist",
            status=AgentStatus.COMPLETED,
            output='{"candidate_id":"cand-1","job_id":"job-1","candidate_name":"Bob","job_title":"Dev","subject":"S","email_body":"E","linkedin_message":"L","short_message":"S"}',
        )

        with patch("app.workflows.outreach.get_registry") as mock_reg:
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

            workflow = OutreachGenerationWorkflow()
            result = await workflow.execute(candidate_id="cand-1", job_id="job-1", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.COMPLETED


class TestBuildInput:
    def test_build_input_all_data(self) -> None:
        workflow = OutreachGenerationWorkflow()
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
        workflow = OutreachGenerationWorkflow()
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
        workflow = OutreachGenerationWorkflow()
        result = workflow._build_input(
            candidate_raw=[{"text": SAMPLE_CANDIDATE_TEXT}],
            job_raw=[{"text": SAMPLE_JOB_TEXT}],
            comments_raw=[{"text": ""}],
        )

        assert "(none)" in result


class TestEndpoint:
    @patch("app.api.v1.ats.OutreachGenerationWorkflow")
    async def test_endpoint_returns_200(self, mock_workflow_cls: MagicMock, client) -> None:
        mock_workflow = AsyncMock()
        mock_workflow.execute.return_value = AgentRunResponse(
            run_id="run-1",
            agent_name="outreach-specialist",
            status=AgentStatus.COMPLETED,
            output='{"candidate_id":"cand-1","job_id":"job-1","candidate_name":"Alice","job_title":"Engineer","subject":"S","email_body":"E","linkedin_message":"L","short_message":"S"}',
        )
        mock_workflow_cls.return_value = mock_workflow

        response = await client.post(
            "/api/v1/generate-outreach",
            json={"candidate_id": "cand-123", "job_id": "job-456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    async def test_endpoint_missing_job_id(self, client) -> None:
        response = await client.post(
            "/api/v1/generate-outreach",
            json={"candidate_id": "cand-123"},
        )
        assert response.status_code == 422
