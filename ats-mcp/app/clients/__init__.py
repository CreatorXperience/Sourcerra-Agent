import asyncio
import random
from typing import Any

import httpx

from app.config import Settings, get_settings
from app.config.logging import get_logger

logger = get_logger(__name__)

RETRYABLE_STATUSES = {429, 502, 503, 504}
MAX_RETRIES = 3
BASE_DELAY = 1.0
MAX_DELAY = 8.0


class BackendClient:
    def __init__(self, settings: Settings | None = None):
        s = settings or get_settings()
        self.base_url = s.BACKEND_API_BASE_URL.rstrip("/")
        self.api_key = s.BACKEND_API_KEY
        self.timeout = s.BACKEND_API_TIMEOUT
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["x-api-key"] = self.api_key
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers=headers,
            )
        return self._client

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        return await self._request("GET", path, params=params)

    async def post(
        self,
        path: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        return await self._request("POST", path, json=data)

    async def put(
        self,
        path: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        return await self._request("PUT", path, json=data)

    async def delete(
        self,
        path: str,
    ) -> dict[str, Any] | list[Any]:
        return await self._request("DELETE", path)

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        client = await self._get_client()
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await client.request(
                    method=method,
                    url=path,
                    params=params,
                    json=json,
                )

                if response.is_success:
                    return response.json()

                if response.status_code == 429:
                    retry_after = _parse_retry_after(response)
                    logger.warning("rate_limited", retry_after=retry_after, attempt=attempt)
                    await asyncio.sleep(retry_after)
                    continue

                if response.status_code in RETRYABLE_STATUSES and attempt < MAX_RETRIES:
                    delay = _backoff_delay(attempt)
                    logger.warning(
                        "retryable_status",
                        status=response.status_code,
                        attempt=attempt,
                        delay=delay,
                    )
                    await asyncio.sleep(delay)
                    continue

                response.raise_for_status()

            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt < MAX_RETRIES:
                    delay = _backoff_delay(attempt)
                    logger.warning("request_timeout", attempt=attempt, delay=delay, path=path)
                    await asyncio.sleep(delay)
                    continue
                raise BackendRequestError(f"Request timed out after {MAX_RETRIES + 1} attempts: {path}") from exc

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status in RETRYABLE_STATUSES and attempt < MAX_RETRIES:
                    delay = _backoff_delay(attempt)
                    logger.warning("http_error_retry", status=status, attempt=attempt, delay=delay)
                    await asyncio.sleep(delay)
                    continue
                raise BackendHTTPError(status, exc.response.text) from exc

            except (httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                last_error = exc
                if attempt < MAX_RETRIES:
                    delay = _backoff_delay(attempt)
                    logger.warning("connection_error", attempt=attempt, delay=delay, path=path)
                    await asyncio.sleep(delay)
                    continue
                raise BackendConnectionError(
                    f"Connection failed after {MAX_RETRIES + 1} attempts: {path}"
                ) from exc

        raise BackendRequestError(f"Request failed after {MAX_RETRIES + 1} attempts: {path}") from last_error

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


class BackendRequestError(Exception):
    pass


class BackendHTTPError(BackendRequestError):
    def __init__(self, status_code: int, body: str = ""):
        self.status_code = status_code
        self.body = body
        super().__init__(f"Backend returned status {status_code}: {body[:200]}")


class BackendConnectionError(BackendRequestError):
    pass


def _backoff_delay(attempt: int) -> float:
    delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter


def _parse_retry_after(response: httpx.Response) -> float:
    value = response.headers.get("Retry-After", "1")
    try:
        return float(value)
    except ValueError:
        return 1.0


_client: BackendClient | None = None


def get_backend_client() -> BackendClient:
    global _client
    if _client is None:
        _client = BackendClient()
    return _client
