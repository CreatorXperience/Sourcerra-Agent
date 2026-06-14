import time
from typing import Any

from app.config.logging import get_logger

logger = get_logger(__name__)


class ToolTracer:
    def __init__(self, enabled: bool = True):
        self._enabled = enabled

    def trace_sync(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        result: Any,
        duration_ms: float,
        error: str | None = None,
    ) -> None:
        if not self._enabled:
            return
        log = logger.info if error is None else logger.warning
        log(
            "tool_call",
            tool=tool_name,
            duration_ms=round(duration_ms, 2),
            has_error=error is not None,
            error=error,
            arg_count=len(arguments),
        )

    def trace_backend_call(
        self,
        method: str,
        path: str,
        duration_ms: float,
        status: int | None = None,
        error: str | None = None,
    ) -> None:
        if not self._enabled:
            return
        log = logger.info if error is None else logger.warning
        log(
            "backend_call",
            method=method,
            path=path,
            duration_ms=round(duration_ms, 2),
            status=status,
            has_error=error is not None,
            error=error,
        )

    async def trace(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        result: Any,
        duration_ms: float,
        error: str | None = None,
    ) -> None:
        self.trace_sync(tool_name, arguments, result, duration_ms, error)


_tracer: ToolTracer | None = None


def get_tracer() -> ToolTracer:
    global _tracer
    if _tracer is None:
        _tracer = ToolTracer(enabled=True)
    return _tracer
