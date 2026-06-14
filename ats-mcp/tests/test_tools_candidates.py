from unittest.mock import AsyncMock

import pytest

from app.tools.candidates import ats_get_candidate, ats_list_candidates


def _make_candidate_raw(overrides: dict | None = None) -> dict:
    base = {
        "id": "cand-1",
        "name": "Alice Engineer",
        "email": "alice@example.com",
        "phone": "+1-555-0100",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "location": "San Francisco, CA",
        "seniority": "senior",
        "lastRole": "Senior Backend Engineer",
        "yearsOfExperience": 7,
        "stage": "INTERVIEW",
        "source": "LINKEDIN",
        "overallScore": 92.5,
        "jobFitScore": 88.0,
        "skillsScore": 95.0,
        "experienceScore": 90.0,
        "summary": "Strong backend engineer with 7+ years experience",
        "recommendation": "strong_yes",
        "resumeUrl": "https://cdn.example.com/resume.pdf",
        "linkedInUrl": "https://linkedin.com/in/alice",
        "jobId": "job-1",
        "companyId": "comp-1",
        "isTopCandidate": True,
    }
    if overrides:
        base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_ats_get_candidate_success(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.return_value = _make_candidate_raw()

    content, is_error = await ats_get_candidate({"candidate_id": "cand-1"})
    assert is_error is False
    assert "Alice Engineer" in content[0]["text"]
    assert "92.5" in content[0]["text"]
    assert "INTERVIEW" in content[0]["text"]


@pytest.mark.asyncio
async def test_ats_get_candidate_not_found(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.return_value = {}

    content, is_error = await ats_get_candidate({"candidate_id": "nonexistent"})
    assert is_error is True


@pytest.mark.asyncio
async def test_ats_get_candidate_connection_error(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.side_effect = Exception("Connection refused")

    content, is_error = await ats_get_candidate({"candidate_id": "cand-1"})
    assert is_error is True


@pytest.mark.asyncio
async def test_ats_get_candidate_invalid_args() -> None:
    content, is_error = await ats_get_candidate({})
    assert is_error is True


@pytest.mark.asyncio
async def test_ats_list_candidates_with_search(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.return_value = [
        _make_candidate_raw({"id": "cand-1", "name": "Alice Engineer"}),
        _make_candidate_raw({"id": "cand-2", "name": "Bob Developer"}),
    ]

    content, is_error = await ats_list_candidates({"search": "engineer", "limit": 20})
    assert is_error is False
    assert "Alice Engineer" in content[0]["text"]
    assert "Bob Developer" in content[0]["text"]


@pytest.mark.asyncio
async def test_ats_list_candidates_with_stage_filter(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.return_value = [
        _make_candidate_raw({"id": "cand-1", "stage": "INTERVIEW"}),
    ]

    content, is_error = await ats_list_candidates({"stage": "INTERVIEW"})
    assert is_error is False


@pytest.mark.asyncio
async def test_ats_list_candidates_with_job_filter(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.return_value = []

    content, is_error = await ats_list_candidates({"job_id": "job-1"})
    assert is_error is False


@pytest.mark.asyncio
async def test_ats_list_candidates_backend_error(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.side_effect = Exception("Backend down")

    content, is_error = await ats_list_candidates({"search": "engineer"})
    assert is_error is True


@pytest.mark.asyncio
async def test_ats_list_candidates_invalid_limit() -> None:
    content, is_error = await ats_list_candidates({"limit": 999})
    assert is_error is True
