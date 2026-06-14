import json
from typing import Any

from app.config.logging import get_logger
from app.config.settings import get_settings

logger = get_logger(__name__)


class CacheService:
    def __init__(self) -> None:
        settings = get_settings()
        self._redis_url = settings.REDIS_URL
        self._client: Any = None
        self._local_cache: dict[str, Any] = {}
        self._enabled = bool(self._redis_url)

    async def initialize(self) -> None:
        if not self._enabled:
            logger.info("cache_disabled", reason="no_redis_url")
            return
        try:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=20,
            )
            await self._client.ping()
            logger.info("cache_connected", url=self._redis_url)
        except Exception as e:
            logger.warning("cache_connect_failed", error=str(e))
            self._enabled = False
            self._client = None

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(self, key: str) -> Any | None:
        if self._client:
            try:
                val = await self._client.get(key)
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.warning("cache_get_failed", key=key, error=str(e))
        return self._local_cache.get(key)

    async def set(
        self, key: str, value: Any, ttl: int = 300
    ) -> None:
        self._local_cache[key] = value
        if self._client:
            try:
                await self._client.setex(key, ttl, json.dumps(value, default=str))
            except Exception as e:
                logger.warning("cache_set_failed", key=key, error=str(e))

    async def delete(self, key: str) -> None:
        self._local_cache.pop(key, None)
        if self._client:
            try:
                await self._client.delete(key)
            except Exception as e:
                logger.warning("cache_delete_failed", key=key, error=str(e))

    async def clear(self) -> None:
        self._local_cache.clear()
        if self._client:
            try:
                await self._client.flushdb()
            except Exception as e:
                logger.warning("cache_clear_failed", error=str(e))

    async def health(self) -> bool:
        if not self._enabled:
            return False
        if not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except Exception:
            return False

    @property
    def is_enabled(self) -> bool:
        return self._enabled


_cache: CacheService | None = None


def get_cache_service() -> CacheService:
    global _cache
    if _cache is None:
        _cache = CacheService()
    return _cache
