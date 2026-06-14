from typing import Any

from app.clients.backend import BackendClient
from app.config.logging import get_logger

logger = get_logger(__name__)


class ResumeService:
    def __init__(self, client: BackendClient):
        self._client = client

    async def get_resume(self, resume_id: str) -> dict[str, Any]:
        return await self._client.get(f"/resumes/{resume_id}")

    async def upload_resume(self, file_url: str, candidate_id: str) -> dict[str, Any]:
        return await self._client.post("/resumes", {
            "file_url": file_url,
            "candidate_id": candidate_id,
        })

    async def extract_text(self, resume_id: str) -> str:
        result = await self._client.get(f"/resumes/{resume_id}/text")
        return result.get("text", "")

    async def get_skills(self, resume_id: str) -> list[str]:
        result = await self._client.get(f"/resumes/{resume_id}/skills")
        return result.get("skills", [])

    async def get_experience(self, resume_id: str) -> list[dict[str, Any]]:
        result = await self._client.get(f"/resumes/{resume_id}/experience")
        return result.get("experience", [])
