from typing import Any

from app.config.logging import get_logger
from app.config.settings import Settings

logger = get_logger(__name__)


class Tracer:
    def __init__(self, settings: Settings):
        self._enabled = not settings.DEBUG

    async def trace_agent_run(
        self,
        agent_name: str,
        input: dict[str, Any],
        output: dict[str, Any],
        duration_ms: float,
    ) -> None:
        if not self._enabled:
            return
        logger.info(
            "agent_trace",
            agent=agent_name,
            duration_ms=round(duration_ms, 2),
        )

    async def trace_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        result: Any,
        duration_ms: float,
        error: str | None = None,
    ) -> None:
        if not self._enabled:
            return
        logger.info(
            "tool_trace",
            tool=tool_name,
            duration_ms=round(duration_ms, 2),
            has_error=error is not None,
        )

    async def trace_llm_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: float,
    ) -> None:
        if not self._enabled:
            return
        logger.info(
            "llm_trace",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            duration_ms=round(duration_ms, 2),
        )


_tracer: Tracer | None = None


def get_tracer(settings: Settings | None = None) -> Tracer:
    global _tracer
    if _tracer is None:
        from app.config.settings import get_settings
        _tracer = Tracer(settings or get_settings())
    return _tracer
