from unittest.mock import AsyncMock

import pytest

from app.tools.jobs import ats_get_job, ats_list_jobs


def _make_job_raw(overrides: dict | None = None) -> dict:
    base = {
        "id": "job-1",
        "title": "Senior Backend Engineer",
        "description": "Build and scale APIs",
        "companyId": "comp-1",
        "automationStatus": True,
        "requirements": [
            {"label": "Python", "fieldType": "skill", "required": True, "options": [], "order": 1},
            {"label": "FastAPI", "fieldType": "skill", "required": True, "options": [], "order": 2},
        ],
        "_count": {"candidates": 12},
    }
    if overrides:
        base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_ats_get_job_success(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.return_value = _make_job_raw()

    content, is_error = await ats_get_job({"job_id": "job-1"})
    assert is_error is False
    assert "Senior Backend Engineer" in content[0]["text"]
    assert "Python" in content[0]["text"]
    assert "12" in content[0]["text"]


@pytest.mark.asyncio
async def test_ats_get_job_not_found(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.return_value = {}

    content, is_error = await ats_get_job({"job_id": "nonexistent"})
    assert is_error is True


@pytest.mark.asyncio
async def test_ats_get_job_connection_error(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.side_effect = Exception("Service unavailable")

    content, is_error = await ats_get_job({"job_id": "job-1"})
    assert is_error is True


@pytest.mark.asyncio
async def test_ats_get_job_missing_id() -> None:
    content, is_error = await ats_get_job({})
    assert is_error is True


@pytest.mark.asyncio
async def test_ats_list_jobs_success(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.return_value = [
        _make_job_raw({"id": "job-1", "title": "Senior Backend Engineer"}),
        _make_job_raw({"id": "job-2", "title": "Frontend Engineer"}),
    ]

    content, is_error = await ats_list_jobs({})
    assert is_error is False
    assert "Senior Backend Engineer" in content[0]["text"]
    assert "Frontend Engineer" in content[0]["text"]


@pytest.mark.asyncio
async def test_ats_list_jobs_empty(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.return_value = []

    content, is_error = await ats_list_jobs({})
    assert is_error is False


@pytest.mark.asyncio
async def test_ats_list_jobs_backend_error(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.side_effect = Exception("Backend down")

    content, is_error = await ats_list_jobs({})
    assert is_error is True
