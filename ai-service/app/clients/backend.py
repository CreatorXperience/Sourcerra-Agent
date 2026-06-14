from typing import Any

import httpx

from app.config.logging import get_logger
from app.config.settings import Settings

logger = get_logger(__name__)


class BackendClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.BACKEND_API_BASE_URL.rstrip("/")
        self.api_key = settings.BACKEND_API_KEY
        self.timeout = settings.BACKEND_API_TIMEOUT
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {
                "Content-Type": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers=headers,
            )
        return self._client

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def post(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post(path, json=data)
        response.raise_for_status()
        return response.json()

    async def put(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.put(path, json=data)
        response.raise_for_status()
        return response.json()

    async def delete(self, path: str) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.delete(path)
        response.raise_for_status()
        return response.json()

    async def is_available(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get("/health")
            return response.is_success
        except Exception:
            return False

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
