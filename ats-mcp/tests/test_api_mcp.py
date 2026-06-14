import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ats-mcp"


@pytest.mark.asyncio
async def test_list_tools_contains_phase1(client: AsyncClient) -> None:
    response = await client.get("/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data

    tool_names = {t["name"] for t in data["tools"]}
    assert "ats_get_candidate" in tool_names
    assert "ats_list_candidates" in tool_names
    assert "ats_get_job" in tool_names
    assert "ats_list_jobs" in tool_names
    assert "ats_get_candidate_comments" in tool_names
    assert "ats_get_candidate_tasks" in tool_names


@pytest.mark.asyncio
async def test_list_tools_contains_phase2_backend_required(client: AsyncClient) -> None:
    response = await client.get("/tools")
    data = response.json()
    tool_names = {t["name"] for t in data["tools"]}

    assert "ats_list_interviews" in tool_names
    assert "ats_get_interview" in tool_names
    assert "ats_schedule_interview" in tool_names
    assert "ats_match_candidates_to_job" in tool_names
    assert "ats_get_analytics_dashboard" in tool_names
    assert "ats_get_resume_processing_status" in tool_names


@pytest.mark.asyncio
async def test_list_tools_phase2_have_backend_required_tag(client: AsyncClient) -> None:
    response = await client.get("/tools")
    data = response.json()
    tools = {t["name"]: t for t in data["tools"]}

    future_tools = [
        "ats_list_interviews", "ats_schedule_interview",
        "ats_get_email_history", "ats_send_email",
        "ats_match_candidates_to_job",
    ]
    for name in future_tools:
        assert "[BACKEND REQUIRED]" in tools[name]["description"]


@pytest.mark.asyncio
async def test_call_unknown_tool_returns_error(client: AsyncClient) -> None:
    response = await client.post(
        "/tools/call",
        json={"name": "nonexistent_tool", "arguments": {}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_error"] is True
    assert "Unknown tool" in data["content"][0]["text"]


@pytest.mark.asyncio
async def test_call_backend_required_tool_returns_not_implemented(client: AsyncClient) -> None:
    response = await client.post(
        "/tools/call",
        json={"name": "ats_schedule_interview", "arguments": {}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_error"] is True


@pytest.mark.asyncio
async def test_tool_input_schemas_have_required_fields(client: AsyncClient) -> None:
    response = await client.get("/tools")
    data = response.json()
    tools = {t["name"]: t for t in data["tools"]}

    assert "candidate_id" in tools["ats_get_candidate"]["input_schema"]["required"]
    assert "job_id" in tools["ats_get_job"]["input_schema"]["required"]
    assert "candidate_id" in tools["ats_get_candidate_comments"]["input_schema"]["required"]
    assert "candidate_id" in tools["ats_get_candidate_tasks"]["input_schema"]["required"]
    assert "interview_id" in tools["ats_get_interview"]["input_schema"]["required"]
    assert "candidate_id" in tools["ats_send_email"]["input_schema"]["required"]
