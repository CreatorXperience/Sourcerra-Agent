from app.agents.base import BaseAgent
from app.schemas.agents import AgentRunResponse, AgentStatus


class ResumeAnalysisAgent(BaseAgent):
    async def run(
        self,
        task: str,
        context: dict | None = None,
    ) -> AgentRunResponse:
        return AgentRunResponse(
            run_id="",
            agent_name=self.config.name,
            status=AgentStatus.COMPLETED,
            output="Resume analysis not yet implemented",
        )
