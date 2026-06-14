from typing import Any

from app.clients.backend import BackendClient
from app.config.logging import get_logger

logger = get_logger(__name__)


class ATSService:
    def __init__(self, client: BackendClient):
        self._client = client

    async def get_candidate(self, candidate_id: str) -> dict[str, Any]:
        return await self._client.get(f"/candidates/{candidate_id}")

    async def search_candidates(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        result = await self._client.get("/candidates", params={"q": query, "limit": limit})
        return result.get("data", result)

    async def get_job(self, job_id: str) -> dict[str, Any]:
        return await self._client.get(f"/jobs/{job_id}")

    async def list_jobs(self, status: str | None = None) -> list[dict[str, Any]]:
        params = {}
        if status:
            params["status"] = status
        result = await self._client.get("/jobs", params=params)
        return result.get("data", result)

    async def get_application(self, application_id: str) -> dict[str, Any]:
        return await self._client.get(f"/applications/{application_id}")

    async def update_application(self, application_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return await self._client.put(f"/applications/{application_id}", data)

    async def create_note(self, application_id: str, content: str) -> dict[str, Any]:
        return await self._client.post(f"/applications/{application_id}/notes", {"content": content})
