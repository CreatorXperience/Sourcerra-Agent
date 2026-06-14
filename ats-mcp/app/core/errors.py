from app.schemas.common import ErrorDetail, ErrorResponse


class ToolError(Exception):
    def __init__(self, code: str, message: str, details: str | None = None):
        self.code = code
        self.message = message
        self.details = details

    def to_response(self) -> ErrorResponse:
        return ErrorResponse(
            error=ErrorDetail(
                code=self.code,
                message=self.message,
                details=self.details,
            )
        )


class NotFoundError(ToolError):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} not found: {resource_id}",
            details=f"No {resource.lower()} exists with the given identifier",
        )


class BackendConnectionError(ToolError):
    def __init__(self, details: str | None = None):
        super().__init__(
            code="BACKEND_CONNECTION_ERROR",
            message="Failed to communicate with backend API",
            details=details,
        )


class BackendResponseError(ToolError):
    def __init__(self, status_code: int, details: str | None = None):
        super().__init__(
            code="BACKEND_RESPONSE_ERROR",
            message=f"Backend API returned status {status_code}",
            details=details,
        )


class BackendTimeoutError(ToolError):
    def __init__(self, details: str | None = None):
        super().__init__(
            code="BACKEND_TIMEOUT",
            message="Backend API request timed out",
            details=details,
        )


class RateLimitError(ToolError):
    def __init__(self, retry_after: float = 1.0):
        super().__init__(
            code="RATE_LIMITED",
            message=f"Rate limited by backend API. Retry after {retry_after}s",
            details=f"Retry-After: {retry_after}",
        )


class NotImplementedError_(ToolError):
    def __init__(self, tool_name: str):
        super().__init__(
            code="NOT_IMPLEMENTED",
            message=f"Tool {tool_name} is not yet implemented",
            details="This capability requires a backend endpoint that does not yet exist",
        )


class ValidationError(ToolError):
    def __init__(self, details: str):
        super().__init__(
            code="VALIDATION_ERROR",
            message="Invalid request parameters",
            details=details,
        )


def tool_error_to_content(error: ToolError) -> tuple[list[dict], bool]:
    text = error.message
    if error.details:
        text = f"{error.message}: {error.details}"
    return [{"type": "text", "text": text}], True
