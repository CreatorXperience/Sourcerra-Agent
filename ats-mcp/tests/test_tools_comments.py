from unittest.mock import AsyncMock

import pytest

from app.tools.comments import ats_get_candidate_comments


@pytest.mark.asyncio
async def test_ats_get_candidate_comments_success(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.return_value = [
        {
            "id": "c-1",
            "content": "Strong technical skills",
            "authorId": "user-1",
            "candidateId": "cand-1",
            "createdAt": "2026-06-01T10:00:00Z",
        },
        {
            "id": "c-2",
            "content": "Good cultural fit",
            "authorId": "user-2",
            "candidateId": "cand-1",
            "createdAt": "2026-06-02T14:00:00Z",
        },
    ]

    content, is_error = await ats_get_candidate_comments({"candidate_id": "cand-1"})
    assert is_error is False
    assert "Strong technical skills" in content[0]["text"]
    assert "Good cultural fit" in content[0]["text"]


@pytest.mark.asyncio
async def test_ats_get_candidate_comments_empty(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.return_value = []

    content, is_error = await ats_get_candidate_comments({"candidate_id": "cand-1"})
    assert is_error is False


@pytest.mark.asyncio
async def test_ats_get_candidate_comments_connection_error(mock_backend_client: AsyncMock) -> None:
    mock_backend_client.get.side_effect = Exception("Timeout")

    content, is_error = await ats_get_candidate_comments({"candidate_id": "cand-1"})
    assert is_error is True


@pytest.mark.asyncio
async def test_ats_get_candidate_comments_missing_candidate_id() -> None:
    content, is_error = await ats_get_candidate_comments({})
    assert is_error is True
