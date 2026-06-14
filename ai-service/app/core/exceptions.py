from fastapi import Request
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorResponse


class AppException(Exception):
    def __init__(self, error: str, detail: str | None = None, status_code: int = 500):
        self.error = error
        self.detail = detail
        self.status_code = status_code


class ConfigurationError(AppException):
    def __init__(self, detail: str | None = None):
        super().__init__(error="configuration_error", detail=detail, status_code=500)


class ProviderError(AppException):
    def __init__(self, detail: str | None = None):
        super().__init__(error="provider_error", detail=detail, status_code=502)


class MCPConnectionError(AppException):
    def __init__(self, detail: str | None = None):
        super().__init__(error="mcp_connection_error", detail=detail, status_code=502)


class AgentExecutionError(AppException):
    def __init__(self, detail: str | None = None):
        super().__init__(error="agent_execution_error", detail=detail, status_code=500)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.error, detail=exc.detail).model_dump(),
    )
