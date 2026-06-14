from typing import Any

from app.config.logging import get_logger
from app.schemas.agents import AgentRunResponse

logger = get_logger(__name__)


class BaseWorkflow:
    def __init__(self):
        self._context: dict[str, Any] = {}

    async def execute(self, **kwargs: Any) -> AgentRunResponse:
        raise NotImplementedError
