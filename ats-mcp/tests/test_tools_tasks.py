from unittest.mock import AsyncMock

import pytest

from app.tools.tasks import ats_get_candidate_tasks


@pytest.mark.asyncio
async def test_ats_get_candidate_tasks_success(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.return_value = [
        {
            "id": "t-1",
            "candidateId": "cand-1",
            "recruiterId": "user-1",
            "companyId": "comp-1",
            "title": "Review resume",
            "description": "Check for relevant experience",
            "status": "DONE",
            "dueDate": "2026-06-10T00:00:00Z",
            "completedAt": "2026-06-09T15:00:00Z",
        },
        {
            "id": "t-2",
            "candidateId": "cand-1",
            "recruiterId": "user-1",
            "companyId": "comp-1",
            "title": "Schedule interview",
            "description": "Find a time slot",
            "status": "TODO",
        },
    ]

    content, is_error = await ats_get_candidate_tasks({"candidate_id": "cand-1"})
    assert is_error is False
    assert "Review resume" in content[0]["text"]
    assert "Schedule interview" in content[0]["text"]


@pytest.mark.asyncio
async def test_ats_get_candidate_tasks_empty(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.return_value = []

    content, is_error = await ats_get_candidate_tasks({"candidate_id": "cand-1"})
    assert is_error is False


@pytest.mark.asyncio
async def test_ats_get_candidate_tasks_connection_error(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.side_effect = Exception("Timeout")

    content, is_error = await ats_get_candidate_tasks({"candidate_id": "cand-1"})
    assert is_error is True


@pytest.mark.asyncio
async def test_ats_get_candidate_tasks_missing_candidate_id() -> None:
    content, is_error = await ats_get_candidate_tasks({})
    assert is_error is True
