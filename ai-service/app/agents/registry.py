
from app.agents.base import BaseAgent
from app.config.logging import get_logger
from app.schemas.agents import AgentConfig, AgentMetadata, AgentStatus, AgentType

logger = get_logger(__name__)


class AgentRegistry:
    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}
        self._configs: dict[str, AgentConfig] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.config.name] = agent
        self._configs[agent.config.name] = agent.config
        logger.info("agent_registered", name=agent.config.name, type=agent.config.agent_type)

    def get(self, name: str) -> BaseAgent | None:
        return self._agents.get(name)

    def list_metadata(self) -> list[AgentMetadata]:
        return [
            AgentMetadata(
                name=config.name,
                type=config.agent_type,
                status=AgentStatus.IDLE,
                model=config.model,
            )
            for config in self._configs.values()
        ]

    def get_by_type(self, agent_type: AgentType) -> list[BaseAgent]:
        return [
            agent
            for agent in self._agents.values()
            if agent.config.agent_type == agent_type
        ]

    @property
    def count(self) -> int:
        return len(self._agents)

    def clear(self) -> None:
        self._agents.clear()
        self._configs.clear()


_registry: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
