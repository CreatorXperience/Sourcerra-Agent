from typing import Any

from app.clients.backend import BackendClient
from app.config.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    def __init__(self, client: BackendClient):
        self._client = client

    async def verify_token(self, token: str) -> dict[str, Any]:
        return await self._client.post("/auth/verify", {"token": token})

    async def get_user(self, user_id: str) -> dict[str, Any]:
        return await self._client.get(f"/users/{user_id}")

    async def has_permission(self, user_id: str, permission: str) -> bool:
        result = await self._client.get(
            f"/users/{user_id}/permissions",
            params={"permission": permission},
        )
        return result.get("granted", False)
