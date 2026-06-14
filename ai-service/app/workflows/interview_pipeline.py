from typing import Any

from app.agents.registry import get_registry
from app.config.logging import get_logger
from app.schemas.agents import AgentRunResponse, AgentStatus
from app.workflows.base import BaseWorkflow

logger = get_logger(__name__)


class InterviewPipelineWorkflow(BaseWorkflow):
    async def execute(self, application_id: str, **kwargs: Any) -> AgentRunResponse:
        registry = get_registry()

        resume_agent = registry.get("resume-analyst")
        interview_agent = registry.get("interview-designer")

        if not resume_agent or not interview_agent:
            return AgentRunResponse(
                run_id="",
                agent_name="interview-pipeline-workflow",
                status=AgentStatus.ERROR,
                error="Required agents not registered",
            )

        logger.info("workflow_started", workflow="interview_pipeline", application_id=application_id)
        return AgentRunResponse(
            run_id="",
            agent_name="interview-pipeline-workflow",
            status=AgentStatus.COMPLETED,
            output="Interview pipeline workflow not yet implemented",
        )
