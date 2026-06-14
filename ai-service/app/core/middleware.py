import time
import uuid
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.logging import get_logger
from app.config.settings import get_settings
from app.core.exceptions import AppException, app_exception_handler

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        start = time.time()
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)

        duration_ms = round((time.time() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Request-Duration-Ms"] = str(duration_ms)

        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, max_requests: int = 60, window: int = 60) -> None:
        super().__init__(app)
        self._max_requests = max_requests
        self._window = window
        self._requests: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        settings = get_settings()
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        cutoff = now - self._window

        if client_ip in self._requests:
            self._requests[client_ip] = [
                t for t in self._requests[client_ip] if t > cutoff
            ]
        else:
            self._requests[client_ip] = []

        if len(self._requests[client_ip]) >= self._max_requests:
            logger.warning("rate_limit_exceeded", client_ip=client_ip)
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limit_exceeded", "detail": "Too many requests"},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        settings = get_settings()
        api_key = settings.API_KEY

        if not api_key:
            return await call_next(request)

        if request.url.path.startswith(("/api/v1/health", "/api/v1/metrics")):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        request_key = auth_header.removeprefix("Bearer ").strip()

        if not request_key:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "detail": "Missing API key"},
            )

        if request_key != api_key:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=403,
                content={"error": "forbidden", "detail": "Invalid API key"},
            )

        return await call_next(request)


def setup_middleware(app: FastAPI) -> None:
    settings = get_settings()

    origins = (
        ["*"]
        if settings.CORS_ORIGINS == "*"
        else [o.strip() for o in settings.CORS_ORIGINS.split(",")]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Request-Duration-Ms"],
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    )
    app.add_middleware(APIKeyMiddleware)

    app.add_exception_handler(AppException, app_exception_handler)
