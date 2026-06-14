import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.recruiter_copilot import RecruiterCopilotAgent
from app.schemas.agents import AgentConfig, AgentRunResponse, AgentStatus, AgentType
from app.schemas.workflows import (
    RecruiterCopilotOutput,
    RecruiterCopilotSynthesis,
)
from app.workflows.recruiter_copilot import RecruiterCopilotWorkflow


@pytest.fixture(autouse=True)
def _mock_openai_client() -> None:
    with patch("app.agents.recruiter_copilot.AsyncOpenAI") as mock_client:
        mock_client.return_value = MagicMock()
        yield


@pytest.fixture
def agent() -> RecruiterCopilotAgent:
    return RecruiterCopilotAgent(
        AgentConfig(name="recruiter-copilot", agent_type=AgentType.GENERAL),
    )


SAMPLE_SUMMARY_OUTPUT = {
    "candidate_name": "Alice Smith",
    "overview": "Senior backend engineer with strong Python skills.",
    "recruiter_observations": ["Excellent communicator"],
    "open_action_items": ["Schedule final interview"],
    "recommended_next_action": "Advance to final round",
}

SAMPLE_DEBRIEF_OUTPUT = {
    "candidate_id": "cand-1",
    "job_id": "job-1",
    "interview_summary": "Alice performed well in both technical and behavioral rounds.",
    "validated_strengths": ["Python depth", "System design"],
    "identified_concerns": ["Kubernetes gap"],
    "further_evaluation_areas": ["Leadership experience"],
    "overall_assessment": "Strong candidate ready for final interview.",
    "recommended_next_step": "Move to Final Interview",
}

SAMPLE_HIRING_OUTPUT = {
    "candidate_id": "cand-1",
    "candidate_name": "Alice Smith",
    "candidate_summary": "Strong backend candidate.",
    "supporting_evidence": ["Technical score 4.5/5"],
    "caution_evidence": ["K8s gap noted"],
    "risk_factors": ["Missing required K8s"],
    "missing_information": ["References pending"],
    "recruiter_recommendation": "Advance with Caution",
    "confidence_level": "High",
}


class TestRecruiterCopilotAgent:
    async def test_agent_registered(self) -> None:
        from app.agents import register_default_agents
        from app.agents.registry import AgentRegistry

        registry = AgentRegistry()
        register_default_agents(registry)
        registered = registry.get("recruiter-copilot")

        assert registered is not None
        assert registered.config.name == "recruiter-copilot"

    @patch("app.agents.recruiter_copilot.Runner.run")
    async def test_run_returns_structured_output(self, mock_run: MagicMock, agent: RecruiterCopilotAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = RecruiterCopilotSynthesis(
            candidate_id="cand-1",
            executive_summary="Alice is a strong backend candidate with minor K8s gap.",
            key_strengths=["Python expertise", "System design skills"],
            key_risks=["Kubernetes experience gap"],
            recommended_next_step="Move to Final Interview",
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="some synthesis input")

        assert result.status == AgentStatus.COMPLETED
        assert result.agent_name == "recruiter-copilot"
        assert result.error is None
        assert "cand-1" in (result.output or "")

    @patch("app.agents.recruiter_copilot.Runner.run")
    async def test_run_includes_all_synthesis_fields(self, mock_run: MagicMock, agent: RecruiterCopilotAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = RecruiterCopilotSynthesis(
            candidate_id="cand-2",
            executive_summary="Executive summary here",
            key_strengths=["S1", "S2", "S3"],
            key_risks=["R1", "R2"],
            recommended_next_step="Hold for Review",
        )
        mock_run.return_value = mock_result

        result = await agent.run(task="data")
        output = json.loads(result.output or "{}")

        assert "executive_summary" in output
        assert "key_strengths" in output
        assert "key_risks" in output
        assert "recommended_next_step" in output
        assert output["candidate_id"] == "cand-2"

    @patch("app.agents.recruiter_copilot.Runner.run")
    async def test_run_loads_prompt_template(self, mock_run: MagicMock, agent: RecruiterCopilotAgent) -> None:
        mock_result = MagicMock()
        mock_result.final_output = RecruiterCopilotSynthesis(
            candidate_id="c-1", executive_summary="S",
            key_strengths=[], key_risks=[], recommended_next_step="Do Not Advance",
        )
        mock_run.return_value = mock_result

        await agent.run(task="data")

        args, _ = mock_run.call_args
        openai_agent = args[0]
        instructions = openai_agent.instructions
        assert "Executive Summary" in instructions
        assert "Key Strengths" in instructions
        assert "Key Risks" in instructions
        assert "Recommended Next Step" in instructions
        assert "synthesize" in instructions.lower()


class TestRecruiterCopilotWorkflow:
    async def test_missing_mcp_manager_returns_error(self) -> None:
        workflow = RecruiterCopilotWorkflow()
        result = await workflow.execute(candidate_id="cand-1", mcp_manager=None)

        assert result.status == AgentStatus.ERROR
        assert result.error and "not available" in result.error

    async def test_happy_path_with_job_id(self) -> None:
        mock_mcp = AsyncMock()

        with (
            patch("app.workflows.recruiter_copilot.CandidateSummaryWorkflow") as mock_summary_cls,
            patch("app.workflows.recruiter_copilot.InterviewDebriefWorkflow") as mock_debrief_cls,
            patch("app.workflows.recruiter_copilot.HiringRecommendationWorkflow") as mock_hiring_cls,
            patch("app.workflows.recruiter_copilot.get_registry") as mock_reg,
        ):
            mock_summary = AsyncMock()
            mock_summary.execute.return_value = AgentRunResponse(
                run_id="s1", agent_name="candidate-summary",
                status=AgentStatus.COMPLETED,
                output=json.dumps(SAMPLE_SUMMARY_OUTPUT),
            )
            mock_summary_cls.return_value = mock_summary

            mock_debrief = AsyncMock()
            mock_debrief.execute.return_value = AgentRunResponse(
                run_id="d1", agent_name="interview-debrief",
                status=AgentStatus.COMPLETED,
                output=json.dumps(SAMPLE_DEBRIEF_OUTPUT),
            )
            mock_debrief_cls.return_value = mock_debrief

            mock_hiring = AsyncMock()
            mock_hiring.execute.return_value = AgentRunResponse(
                run_id="h1", agent_name="hiring-recommendation",
                status=AgentStatus.COMPLETED,
                output=json.dumps(SAMPLE_HIRING_OUTPUT),
            )
            mock_hiring_cls.return_value = mock_hiring

            mock_copilot = AsyncMock()
            mock_copilot.run.return_value = AgentRunResponse(
                run_id="c1", agent_name="recruiter-copilot",
                status=AgentStatus.COMPLETED,
                output=json.dumps({
                    "candidate_id": "cand-1",
                    "executive_summary": "Alice is a strong candidate.",
                    "key_strengths": ["Python", "System design"],
                    "key_risks": ["K8s gap"],
                    "recommended_next_step": "Move to Final Interview",
                }),
            )
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_copilot
            mock_reg.return_value = mock_registry

            workflow = RecruiterCopilotWorkflow()
            result = await workflow.execute(
                candidate_id="cand-1", job_id="job-1", mcp_manager=mock_mcp,
            )

        assert result.status == AgentStatus.COMPLETED
        data = json.loads(result.output or "{}")
        assert data["candidate_id"] == "cand-1"
        assert data["candidate_overview"] is not None
        assert data["interview_assessment"] is not None
        assert data["hiring_recommendation"] is not None
        assert data["executive_summary"] == "Alice is a strong candidate."
        assert "Move to Final Interview" in data["recommended_next_step"]
        assert len(data["key_strengths"]) == 2

    async def test_happy_path_without_job_id(self) -> None:
        mock_mcp = AsyncMock()

        with (
            patch("app.workflows.recruiter_copilot.CandidateSummaryWorkflow") as mock_summary_cls,
            patch("app.workflows.recruiter_copilot.InterviewDebriefWorkflow") as mock_debrief_cls,
            patch("app.workflows.recruiter_copilot.HiringRecommendationWorkflow") as mock_hiring_cls,
            patch("app.workflows.recruiter_copilot.get_registry") as mock_reg,
        ):
            mock_summary = AsyncMock()
            mock_summary.execute.return_value = AgentRunResponse(
                run_id="s1", agent_name="candidate-summary",
                status=AgentStatus.COMPLETED,
                output=json.dumps(SAMPLE_SUMMARY_OUTPUT),
            )
            mock_summary_cls.return_value = mock_summary

            mock_hiring = AsyncMock()
            mock_hiring.execute.return_value = AgentRunResponse(
                run_id="h1", agent_name="hiring-recommendation",
                status=AgentStatus.COMPLETED,
                output=json.dumps(SAMPLE_HIRING_OUTPUT),
            )
            mock_hiring_cls.return_value = mock_hiring

            mock_copilot = AsyncMock()
            mock_copilot.run.return_value = AgentRunResponse(
                run_id="c1", agent_name="recruiter-copilot",
                status=AgentStatus.COMPLETED,
                output=json.dumps({
                    "candidate_id": "cand-1",
                    "executive_summary": "Alice is a strong candidate.",
                    "key_strengths": ["Python"],
                    "key_risks": ["K8s gap"],
                    "recommended_next_step": "Advance with Caution",
                }),
            )
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_copilot
            mock_reg.return_value = mock_registry

            workflow = RecruiterCopilotWorkflow()
            result = await workflow.execute(
                candidate_id="cand-1", mcp_manager=mock_mcp,
            )

        assert result.status == AgentStatus.COMPLETED
        data = json.loads(result.output or "{}")
        assert data["candidate_id"] == "cand-1"
        assert data["candidate_overview"] is not None
        assert data["interview_assessment"] is None
        assert data["hiring_recommendation"] is not None
        mock_debrief_cls.execute  # lint: debrief should NOT be called

    async def test_sub_workflow_failure_graceful(self) -> None:
        mock_mcp = AsyncMock()

        with (
            patch("app.workflows.recruiter_copilot.CandidateSummaryWorkflow") as mock_summary_cls,
            patch("app.workflows.recruiter_copilot.InterviewDebriefWorkflow") as mock_debrief_cls,
            patch("app.workflows.recruiter_copilot.HiringRecommendationWorkflow") as mock_hiring_cls,
            patch("app.workflows.recruiter_copilot.get_registry") as mock_reg,
        ):
            mock_summary = AsyncMock()
            mock_summary.execute = AsyncMock(return_value=AgentRunResponse(
                run_id="s1", agent_name="candidate-summary",
                status=AgentStatus.ERROR,
                error="Candidate not found",
            ))
            mock_summary_cls.return_value = mock_summary

            mock_debrief = AsyncMock()
            mock_debrief.execute = AsyncMock(return_value=AgentRunResponse(
                run_id="d1", agent_name="interview-debrief",
                status=AgentStatus.COMPLETED,
                output=json.dumps(SAMPLE_DEBRIEF_OUTPUT),
            ))
            mock_debrief_cls.return_value = mock_debrief

            mock_hiring = AsyncMock()
            mock_hiring.execute = AsyncMock(return_value=AgentRunResponse(
                run_id="h1", agent_name="hiring-recommendation",
                status=AgentStatus.COMPLETED,
                output=json.dumps(SAMPLE_HIRING_OUTPUT),
            ))
            mock_hiring_cls.return_value = mock_hiring

            mock_copilot = AsyncMock()
            mock_copilot.run.return_value = AgentRunResponse(
                run_id="c1", agent_name="recruiter-copilot",
                status=AgentStatus.COMPLETED,
                output=json.dumps({
                    "candidate_id": "cand-1",
                    "executive_summary": "Limited data available.",
                    "key_strengths": [],
                    "key_risks": ["Missing candidate data"],
                    "recommended_next_step": "Gather Additional Information",
                }),
            )
            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_copilot
            mock_reg.return_value = mock_registry

            workflow = RecruiterCopilotWorkflow()
            result = await workflow.execute(
                candidate_id="cand-1", job_id="job-1", mcp_manager=mock_mcp,
            )

        assert result.status == AgentStatus.COMPLETED
        data = json.loads(result.output or "{}")
        assert data["candidate_overview"] is None
        assert data["hiring_recommendation"] is not None

    async def test_missing_copilot_agent_returns_error(self) -> None:
        mock_mcp = AsyncMock()

        with (
            patch("app.workflows.recruiter_copilot.CandidateSummaryWorkflow") as mock_summary_cls,
            patch("app.workflows.recruiter_copilot.InterviewDebriefWorkflow") as mock_debrief_cls,
            patch("app.workflows.recruiter_copilot.HiringRecommendationWorkflow") as mock_hiring_cls,
            patch("app.workflows.recruiter_copilot.get_registry") as mock_reg,
        ):
            mock_summary = AsyncMock()
            mock_summary.execute = AsyncMock(return_value=AgentRunResponse(
                run_id="s1", agent_name="candidate-summary",
                status=AgentStatus.COMPLETED,
                output=json.dumps(SAMPLE_SUMMARY_OUTPUT),
            ))
            mock_summary_cls.return_value = mock_summary

            mock_debrief = AsyncMock()
            mock_debrief.execute = AsyncMock(return_value=AgentRunResponse(
                run_id="d1", agent_name="interview-debrief",
                status=AgentStatus.COMPLETED,
                output=json.dumps(SAMPLE_DEBRIEF_OUTPUT),
            ))
            mock_debrief_cls.return_value = mock_debrief

            mock_hiring = AsyncMock()
            mock_hiring.execute = AsyncMock(return_value=AgentRunResponse(
                run_id="h1", agent_name="hiring-recommendation",
                status=AgentStatus.COMPLETED,
                output=json.dumps(SAMPLE_HIRING_OUTPUT),
            ))
            mock_hiring_cls.return_value = mock_hiring

            mock_registry = MagicMock()
            mock_registry.get.return_value = None
            mock_reg.return_value = mock_registry

            workflow = RecruiterCopilotWorkflow()
            result = await workflow.execute(
                candidate_id="cand-1", job_id="job-1", mcp_manager=mock_mcp,
            )

        assert result.status == AgentStatus.ERROR
        assert "not registered" in (result.error or "")


class TestBuildSynthesisInput:
    def test_all_data_present(self) -> None:
        workflow = RecruiterCopilotWorkflow()
        result = workflow._build_synthesis_input(
            summary_data=SAMPLE_SUMMARY_OUTPUT,
            debrief_data=SAMPLE_DEBRIEF_OUTPUT,
            hiring_data=SAMPLE_HIRING_OUTPUT,
        )

        assert "CANDIDATE OVERVIEW" in result
        assert "INTERVIEW ASSESSMENT" in result
        assert "HIRING RECOMMENDATION" in result
        assert "Alice Smith" in result
        assert "Excellent communicator" in result

    def test_some_data_missing(self) -> None:
        workflow = RecruiterCopilotWorkflow()
        result = workflow._build_synthesis_input(
            summary_data=None,
            debrief_data=SAMPLE_DEBRIEF_OUTPUT,
            hiring_data=None,
        )

        assert "CANDIDATE OVERVIEW" in result
        assert "(not available)" in result
        assert "INTERVIEW ASSESSMENT" in result
        assert "HIRING RECOMMENDATION" in result
        assert "(not available)" in result

    def test_all_data_missing(self) -> None:
        workflow = RecruiterCopilotWorkflow()
        result = workflow._build_synthesis_input(
            summary_data=None,
            debrief_data=None,
            hiring_data=None,
        )

        assert "(not available)" in result


class TestSafeParse:
    def test_successful_response(self) -> None:
        workflow = RecruiterCopilotWorkflow()
        response = AgentRunResponse(
            run_id="r1", agent_name="test",
            status=AgentStatus.COMPLETED,
            output=json.dumps({"key": "value"}),
        )
        result = workflow._safe_parse(response, "test")
        assert result == {"key": "value"}

    def test_error_response(self) -> None:
        workflow = RecruiterCopilotWorkflow()
        response = AgentRunResponse(
            run_id="r1", agent_name="test",
            status=AgentStatus.ERROR, error="Something failed",
        )
        result = workflow._safe_parse(response, "test")
        assert result is None

    def test_none_result(self) -> None:
        workflow = RecruiterCopilotWorkflow()
        result = workflow._safe_parse(None, "test")
        assert result is None

    def test_exception_result(self) -> None:
        workflow = RecruiterCopilotWorkflow()
        result = workflow._safe_parse(RuntimeError("fail"), "test")
        assert result is None

    def test_invalid_json(self) -> None:
        workflow = RecruiterCopilotWorkflow()
        response = AgentRunResponse(
            run_id="r1", agent_name="test",
            status=AgentStatus.COMPLETED,
            output="not-json",
        )
        result = workflow._safe_parse(response, "test")
        assert result is None


class TestEndpoint:
    @patch("app.api.v1.ats.RecruiterCopilotWorkflow")
    async def test_endpoint_returns_200(self, mock_workflow_cls: MagicMock, client) -> None:
        mock_workflow = AsyncMock()
        mock_workflow.execute.return_value = AgentRunResponse(
            run_id="run-1",
            agent_name="recruiter-copilot",
            status=AgentStatus.COMPLETED,
            output=json.dumps({
                "candidate_id": "cand-1",
                "executive_summary": "Strong candidate overall.",
                "candidate_overview": SAMPLE_SUMMARY_OUTPUT,
                "interview_assessment": SAMPLE_DEBRIEF_OUTPUT,
                "hiring_recommendation": SAMPLE_HIRING_OUTPUT,
                "key_strengths": ["Python", "System design"],
                "key_risks": ["K8s gap"],
                "recommended_next_step": "Move to Final Interview",
            }),
        )
        mock_workflow_cls.return_value = mock_workflow

        response = await client.post(
            "/api/v1/recruiter-copilot",
            json={"candidate_id": "cand-123", "job_id": "job-456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    async def test_endpoint_works_without_job_id(self, client) -> None:
        mock_workflow = AsyncMock()

        with patch("app.api.v1.ats.RecruiterCopilotWorkflow") as mock_workflow_cls:
            mock_workflow.execute.return_value = AgentRunResponse(
                run_id="run-1", agent_name="recruiter-copilot",
                status=AgentStatus.COMPLETED,
                output=json.dumps({
                    "candidate_id": "cand-1",
                    "executive_summary": "S", "candidate_overview": {},
                    "key_strengths": [], "key_risks": [],
                    "recommended_next_step": "Hold for Review",
                }),
            )
            mock_workflow_cls.return_value = mock_workflow

            response = await client.post(
                "/api/v1/recruiter-copilot",
                json={"candidate_id": "cand-123"},
            )
        assert response.status_code == 200

    async def test_endpoint_missing_candidate_id(self, client) -> None:
        response = await client.post(
            "/api/v1/recruiter-copilot",
            json={"job_id": "job-456"},
        )
        assert response.status_code == 422

    async def test_endpoint_empty_body(self, client) -> None:
        response = await client.post(
            "/api/v1/recruiter-copilot",
            json={},
        )
        assert response.status_code == 422
