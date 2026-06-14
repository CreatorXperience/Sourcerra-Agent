
from app.agents.registry import get_registry
from app.config.logging import get_logger
from app.schemas.agents import AgentRunRequest, AgentRunResponse, AgentStatus

logger = get_logger(__name__)


class AgentOrchestrator:
    def __init__(self):
        self._registry = get_registry()

    async def run_agent(self, request: AgentRunRequest) -> AgentRunResponse:
        agent = self._registry.get(request.agent_name)
        if not agent:
            return AgentRunResponse(
                run_id="",
                agent_name=request.agent_name,
                status=AgentStatus.ERROR,
                error=f"Agent not found: {request.agent_name}",
            )

        logger.info(
            "agent_execution_started",
            agent=request.agent_name,
            task_length=len(request.task),
        )

        try:
            response = await agent.run(task=request.task, context=request.context)
            return response
        except Exception as exc:
            logger.error(
                "agent_execution_failed",
                agent=request.agent_name,
                error=str(exc),
            )
            return AgentRunResponse(
                run_id="",
                agent_name=request.agent_name,
                status=AgentStatus.ERROR,
                error=str(exc),
            )


_orchestrator: AgentOrchestrator | None = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
