from abc import ABC, abstractmethod
from typing import Any

from app.schemas.agents import AgentConfig, AgentRunResponse


class BaseAgent(ABC):
    def __init__(self, config: AgentConfig):
        self.config = config

    @abstractmethod
    async def run(self, task: str, context: dict[str, Any] | None = None) -> AgentRunResponse:
        ...
