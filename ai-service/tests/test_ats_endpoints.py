from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.schemas.agents import AgentRunResponse, AgentStatus


@patch("app.api.v1.ats.MatchCandidatesWorkflow")
async def test_candidate_match_endpoint(mock_workflow_cls: MagicMock, client: AsyncClient) -> None:
    mock_workflow = AsyncMock()
    mock_workflow.execute.return_value = AgentRunResponse(
        run_id="run-1",
        agent_name="candidate-matcher",
        status=AgentStatus.COMPLETED,
        output='{"job_id":"job-1","job_title":"Senior Engineer","top_candidates":[{"candidate_id":"cand-1","candidate_name":"Alice","overall_score":92.0,"ranking":1,"explanation":"Top match"}]}',
    )
    mock_workflow_cls.return_value = mock_workflow

    response = await client.post(
        "/api/v1/candidate-match",
        json={"job_id": "job-123", "limit": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "job-1" in data["output"]


async def test_candidate_match_invalid_limit(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/candidate-match",
        json={"job_id": "job-123", "limit": 0},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_resume_analysis_endpoint(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/resume-analysis",
        json={"resume_id": "res-123"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.api.v1.ats.OutreachGenerationWorkflow")
async def test_generate_outreach_endpoint(mock_workflow_cls: MagicMock, client: AsyncClient) -> None:
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


@pytest.mark.asyncio
async def test_generate_interview_endpoint(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/generate-interview",
        json={"job_id": "job-123", "question_count": 5},
    )
    assert response.status_code == 200


@patch("app.api.v1.ats.InterviewQuestionWorkflow")
async def test_generate_interview_questions_endpoint(
    mock_workflow_cls: MagicMock, client: AsyncClient,
) -> None:
    mock_workflow = AsyncMock()
    mock_workflow.execute.return_value = AgentRunResponse(
        run_id="run-1",
        agent_name="interview-question-generator",
        status=AgentStatus.COMPLETED,
        output='{"candidate_id":"cand-1","job_id":"job-1","job_title":"Engineer","technical_questions":[],"behavioral_questions":[],"follow_up_questions":[],"focus_areas":[]}',
    )
    mock_workflow_cls.return_value = mock_workflow

    response = await client.post(
        "/api/v1/generate-interview-questions",
        json={"candidate_id": "cand-123", "job_id": "job-456"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


async def test_generate_interview_questions_missing_fields(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/generate-interview-questions",
        json={"candidate_id": "cand-123"},
    )
    assert response.status_code == 422

    response = await client.post(
        "/api/v1/generate-interview-questions",
        json={"job_id": "job-456"},
    )
    assert response.status_code == 422


@patch("app.api.v1.ats.CandidateSummaryWorkflow")
async def test_candidate_summary_endpoint(mock_workflow_cls: MagicMock, client: AsyncClient) -> None:
    mock_workflow = AsyncMock()
    mock_workflow.execute.return_value = AgentRunResponse(
        run_id="run-1",
        agent_name="candidate-summarizer",
        status=AgentStatus.COMPLETED,
        output='{"candidate_name":"Alice","overview":"Senior engineer","recruiter_observations":["Good communicator"],"open_action_items":["Schedule interview"],"recommended_next_action":"Proceed"}',
    )
    mock_workflow_cls.return_value = mock_workflow

    response = await client.post(
        "/api/v1/candidate-summary",
        json={"candidate_id": "cand-123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "Alice" in data["output"]


async def test_candidate_summary_missing_id(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/candidate-summary",
        json={},
    )
    assert response.status_code == 422
