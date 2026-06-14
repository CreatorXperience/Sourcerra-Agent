import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded", "unhealthy")
    assert "uptime_seconds" in data
    assert "version" in data
    assert "dependencies" in data


@pytest.mark.asyncio
async def test_health_live(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "uptime_seconds" in data


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "unhealthy")
    assert "dependencies" in data


@pytest.mark.asyncio
async def test_health_dependencies_structure(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    data = response.json()
    deps = data["dependencies"]
    dep_names = [d["name"] for d in deps]
    assert "llm_provider" in dep_names
    assert "cache" in dep_names
    assert "evaluation_store" in dep_names


@pytest.mark.asyncio
async def test_tools_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/tools")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
