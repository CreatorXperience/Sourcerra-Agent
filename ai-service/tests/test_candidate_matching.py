import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.candidate_matching import CandidateMatchingAgent
from app.schemas.agents import AgentConfig, AgentRunResponse, AgentStatus, AgentType
from app.schemas.tools import ToolCallStatus, ToolResult
from app.schemas.workflows import CandidateMatchOutput, CandidateResult
from app.workflows.match_candidates import MatchCandidatesWorkflow


@pytest.fixture(autouse=True)
def _mock_openai_client() -> None:
    with patch("app.agents.candidate_matching.AsyncOpenAI") as mock_client:
        mock_client.return_value = MagicMock()
        yield


@pytest.fixture
def agent() -> CandidateMatchingAgent:
    return CandidateMatchingAgent(
        AgentConfig(name="candidate-matcher", agent_type=AgentType.CANDIDATE_MATCHING),
    )


SAMPLE_CANDIDATES = [
    {
        "id": "cand-1",
        "name": "Alice Smith",
        "overall_score": 92.0,
        "job_fit_score": 90.0,
        "skills_score": 95.0,
        "experience_score": 88.0,
        "skills": ["Python", "AWS", "Docker"],
        "top_skills_match": ["Python", "AWS"],
        "missing_skills": ["Kubernetes"],
        "strengths": ["Strong backend experience", "Excellent problem solver"],
        "weaknesses": ["No cloud orchestration experience"],
        "recommendation": "strong_yes",
        "stage": "INTERVIEW",
    },
    {
        "id": "cand-2",
        "name": "Bob Jones",
        "overall_score": 78.5,
        "job_fit_score": 75.0,
        "skills_score": 80.0,
        "experience_score": 70.0,
        "skills": ["Python", "FastAPI"],
        "top_skills_match": ["Python"],
        "missing_skills": ["AWS", "Docker"],
        "strengths": ["Fast learner"],
        "weaknesses": ["Limited cloud experience"],
        "recommendation": "yes",
        "stage": "SCREENED",
    },
    {
        "id": "cand-3",
        "name": "Carol Davis",
        "overall_score": None,
        "job_fit_score": None,
        "skills_score": None,
        "experience_score": None,
        "skills": [],
        "top_skills_match": [],
        "missing_skills": [],
        "strengths": [],
        "weaknesses": [],
        "recommendation": None,
        "stage": "APPLIED",
    },
]

SAMPLE_JOB_LIST_RESPONSE = json.dumps({
    "candidates": SAMPLE_CANDIDATES,
    "total": 3,
    "limit": 200,
})

SAMPLE_JOB_TEXT = json.dumps({
    "id": "job-1",
    "title": "Senior Python Backend Engineer",
    "description": "Build and maintain backend services",
    "company_id": "comp-1",
    "automation_status": False,
    "requirements": [
        {"label": "Python", "field_type": "skill", "required": True},
        {"label": "AWS", "field_type": "skill", "required": True},
    ],
    "candidate_count": 3,
})


class TestCandidateMatchingAgent:
    async def test_agent_registered(self) -> None:
        from app.agents import register_default_agents
        from app.agents.registry import AgentRegistry

        registry = AgentRegistry()
        register_default_agents(registry)
        registered = registry.get("candidate-matcher")

        assert registered is not None
        assert registered.config.name == "candidate-matcher"
        assert registered.config.agent_type == AgentType.CANDIDATE_MATCHING

    @patch("app.agents.candidate_matching.Runner.run")
    async def test_run_returns_structured_output(self, mock_run: MagicMock, agent: CandidateMatchingAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = CandidateMatchOutput(
            job_id="job-1",
            job_title="Senior Python Backend Engineer",
            top_candidates=[
                CandidateResult(
                    candidate_id="cand-1",
                    candidate_name="Alice Smith",
                    overall_score=92.0,
                    job_fit_score=90.0,
                    skills_score=95.0,
                    experience_score=88.0,
                    ranking=1,
                    strengths=["Strong backend experience", "Excellent problem solver"],
                    weaknesses=["No cloud orchestration experience"],
                    explanation="Alice scores 92 overall with excellent skills match (95) for the Senior Python Backend Engineer role. Strong Python and AWS experience align directly with key requirements.",
                ),
            ],
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="some candidate data")

        assert result.status == AgentStatus.COMPLETED
        assert result.agent_name == "candidate-matcher"
        assert result.error is None
        assert "Alice Smith" in (result.output or "")

    @patch("app.agents.candidate_matching.Runner.run")
    async def test_run_handles_none_scores(self, mock_run: MagicMock, agent: CandidateMatchingAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = CandidateMatchOutput(
            job_id="job-1",
            job_title="Test Job",
            top_candidates=[
                CandidateResult(
                    candidate_id="cand-3",
                    candidate_name="Carol Davis",
                    overall_score=None,
                    job_fit_score=None,
                    skills_score=None,
                    experience_score=None,
                    ranking=1,
                    strengths=[],
                    weaknesses=[],
                    explanation="Carol has no scoring data available yet as she is in the APPLIED stage.",
                ),
            ],
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="candidate with missing scores")

        assert result.status == AgentStatus.COMPLETED
        assert "Carol" in (result.output or "")

    @patch("app.agents.candidate_matching.Runner.run")
    async def test_run_loads_prompt_template(self, mock_run: MagicMock, agent: CandidateMatchingAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = CandidateMatchOutput(
            job_id="j-1", job_title="Test", top_candidates=[],
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="data")

        assert result.status == AgentStatus.COMPLETED
        args, _ = mock_run.call_args
        openai_agent = args[0]
        instructions = openai_agent.instructions
        assert "overall_score" in instructions
        assert "explanation" in instructions
        assert "re-rank" in instructions

    @patch("app.agents.candidate_matching.Runner.run")
    async def test_run_includes_all_required_fields(self, mock_run: MagicMock, agent: CandidateMatchingAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = CandidateMatchOutput(
            job_id="job-1",
            job_title="Senior Engineer",
            top_candidates=[
                CandidateResult(
                    candidate_id="cand-1",
                    candidate_name="Alice",
                    overall_score=92.0,
                    job_fit_score=90.0,
                    skills_score=95.0,
                    experience_score=88.0,
                    ranking=1,
                    strengths=["Python"],
                    weaknesses=["No K8s"],
                    explanation="Alice has strong Python skills matching the role requirements.",
                ),
            ],
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="data")
        output = json.loads(result.output or "{}")

        assert "job_id" in output
        assert "job_title" in output
        assert "top_candidates" in output
        assert len(output["top_candidates"]) == 1
        entry = output["top_candidates"][0]
        assert "candidate_id" in entry
        assert "candidate_name" in entry
        assert "ranking" in entry
        assert "explanation" in entry
        assert "overall_score" in entry


class TestMatchCandidatesWorkflow:
    async def test_missing_agent_returns_error(self) -> None:
        with patch("app.workflows.match_candidates.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = None
            mock_reg.return_value = mock_registry

            workflow = MatchCandidatesWorkflow()
            result = await workflow.execute(job_id="job-1")

        assert result.status == AgentStatus.ERROR
        assert result.error and "not registered" in result.error

    async def test_missing_mcp_manager_returns_error(self) -> None:
        with patch("app.workflows.match_candidates.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = MagicMock()
            mock_reg.return_value = mock_registry

            workflow = MatchCandidatesWorkflow()
            result = await workflow.execute(job_id="job-1", mcp_manager=None)

        assert result.status == AgentStatus.ERROR
        assert result.error and "not available" in result.error

    async def test_missing_job_returns_error(self) -> None:
        mock_agent = MagicMock()

        with patch("app.workflows.match_candidates.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_agent
            mock_reg.return_value = mock_registry

            mock_mcp = AsyncMock()

            async def mock_call_tool(name: str, args: dict) -> ToolResult:
                if name == "ats_get_job":
                    return ToolResult(status=ToolCallStatus.ERROR, error="Job not found")
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown")

            mock_mcp.call_tool = mock_call_tool

            workflow = MatchCandidatesWorkflow()
            result = await workflow.execute(job_id="bad-job", mcp_manager=mock_mcp)

        assert result.status == AgentStatus.ERROR
        assert "not found" in (result.error or "")

    async def test_happy_path_with_ranked_candidates(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.run.return_value = AgentRunResponse(
            run_id="run-1",
            agent_name="candidate-matcher",
            status=AgentStatus.COMPLETED,
            output='{"job_id":"job-1","job_title":"Senior Engineer","top_candidates":[{"candidate_id":"cand-1","candidate_name":"Alice Smith","overall_score":92.0,"ranking":1,"explanation":"Top match"}]}',
        )

        with patch("app.workflows.match_candidates.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_agent
            mock_reg.return_value = mock_registry

            mock_mcp = AsyncMock()

            async def mock_call_tool(name: str, args: dict) -> ToolResult:
                if name == "ats_get_job":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_JOB_TEXT}])
                if name == "ats_list_candidates":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_JOB_LIST_RESPONSE}])
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown")

            mock_mcp.call_tool = mock_call_tool

            workflow = MatchCandidatesWorkflow()
            result = await workflow.execute(job_id="job-1", mcp_manager=mock_mcp, limit=10)

        assert result.status == AgentStatus.COMPLETED
        assert result.output and "job-1" in result.output
        mock_agent.run.assert_called_once()

    async def test_sorts_by_overall_score_desc(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.run.return_value = AgentRunResponse(
            run_id="run-2",
            agent_name="candidate-matcher",
            status=AgentStatus.COMPLETED,
            output="{}",
        )

        with patch("app.workflows.match_candidates.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_agent
            mock_reg.return_value = mock_registry

            mock_mcp = AsyncMock()

            async def mock_call_tool(name: str, args: dict) -> ToolResult:
                if name == "ats_get_job":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_JOB_TEXT}])
                if name == "ats_list_candidates":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_JOB_LIST_RESPONSE}])
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown")

            mock_mcp.call_tool = mock_call_tool

            workflow = MatchCandidatesWorkflow()
            result = await workflow.execute(job_id="job-1", mcp_manager=mock_mcp, limit=2)

        assert result.status == AgentStatus.COMPLETED
        call_kwargs = mock_agent.run.call_args
        task_text = call_kwargs[1]["task"]
        assert "Alice Smith" in task_text
        assert "Bob Jones" in task_text
        alice_pos = task_text.index("Alice Smith")
        bob_pos = task_text.index("Bob Jones")
        assert alice_pos < bob_pos

    async def test_handles_no_candidates_gracefully(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.run.return_value = AgentRunResponse(
            run_id="run-3",
            agent_name="candidate-matcher",
            status=AgentStatus.COMPLETED,
            output='{"job_id":"job-1","job_title":"Test","top_candidates":[]}',
        )

        with patch("app.workflows.match_candidates.get_registry") as mock_reg:
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_agent
            mock_reg.return_value = mock_registry

            mock_mcp = AsyncMock()

            async def mock_call_tool(name: str, args: dict) -> ToolResult:
                if name == "ats_get_job":
                    return ToolResult(status=ToolCallStatus.SUCCESS, output=[{"text": SAMPLE_JOB_TEXT}])
                if name == "ats_list_candidates":
                    return ToolResult(status=ToolCallStatus.ERROR, error="No candidates")
                return ToolResult(status=ToolCallStatus.ERROR, error="Unknown")

            mock_mcp.call_tool = mock_call_tool

            workflow = MatchCandidatesWorkflow()
            result = await workflow.execute(job_id="job-1", mcp_manager=mock_mcp, limit=10)

        assert result.status == AgentStatus.COMPLETED


class TestBuildInput:
    def test_build_input_with_candidates(self) -> None:
        workflow = MatchCandidatesWorkflow()
        result = workflow._build_input(
            job_raw=[{"text": SAMPLE_JOB_TEXT}],
            candidates_raw=[{"text": SAMPLE_JOB_LIST_RESPONSE}],
            limit=2,
        )

        assert "JOB INFORMATION" in result
        assert "TOP 2 CANDIDATES" in result
        assert "Senior Python Backend Engineer" in result
        assert "Alice Smith" in result
        assert "Bob Jones" in result
        assert "Carol Davis" not in result

    def test_build_input_respects_limit(self) -> None:
        workflow = MatchCandidatesWorkflow()
        result = workflow._build_input(
            job_raw=[{"text": SAMPLE_JOB_TEXT}],
            candidates_raw=[{"text": SAMPLE_JOB_LIST_RESPONSE}],
            limit=1,
        )

        assert "TOP 1 CANDIDATES" in result
        assert "Alice Smith" in result
        assert "Bob Jones" not in result

    def test_build_input_no_candidates(self) -> None:
        workflow = MatchCandidatesWorkflow()
        result = workflow._build_input(
            job_raw=[{"text": SAMPLE_JOB_TEXT}],
            candidates_raw=None,
            limit=10,
        )

        assert "JOB INFORMATION" in result
        assert "no candidates found" in result

    def test_sort_correctly_orders_by_score(self) -> None:
        reversed_data = json.dumps({
            "candidates": list(reversed(SAMPLE_CANDIDATES)),
            "total": 3,
            "limit": 200,
        })
        workflow = MatchCandidatesWorkflow()
        result = workflow._build_input(
            job_raw=[{"text": SAMPLE_JOB_TEXT}],
            candidates_raw=[{"text": reversed_data}],
            limit=3,
        )

        alice_pos = result.index("Alice Smith")
        bob_pos = result.index("Bob Jones")
        carol_pos = result.index("Carol Davis")
        assert alice_pos < bob_pos
        assert bob_pos < carol_pos


class TestParseCandidates:
    def test_parse_dict_response(self) -> None:
        workflow = MatchCandidatesWorkflow()
        result = workflow._parse_candidates([{"text": SAMPLE_JOB_LIST_RESPONSE}])

        assert len(result) == 3
        assert result[0]["id"] == "cand-1"
        assert result[1]["id"] == "cand-2"

    def test_parse_missing_text(self) -> None:
        workflow = MatchCandidatesWorkflow()
        result = workflow._parse_candidates([])

        assert result == []

    def test_parse_invalid_json(self) -> None:
        workflow = MatchCandidatesWorkflow()
        result = workflow._parse_candidates([{"text": "not json"}])

        assert result == []
