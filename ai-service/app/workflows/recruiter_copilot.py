import asyncio
import json
from typing import Any

from app.agents.registry import get_registry
from app.config.logging import get_logger
from app.mcp.client import MCPClientManager
from app.schemas.agents import AgentRunResponse, AgentStatus
from app.schemas.workflows import RecruiterCopilotOutput
from app.workflows.candidate_summary import CandidateSummaryWorkflow
from app.workflows.hiring_recommendation import HiringRecommendationWorkflow
from app.workflows.interview_debrief import InterviewDebriefWorkflow

logger = get_logger(__name__)


class RecruiterCopilotWorkflow:
    async def execute(
        self,
        candidate_id: str,
        job_id: str | None = None,
        mcp_manager: MCPClientManager | None = None,
        **kwargs: Any,
    ) -> AgentRunResponse:
        if mcp_manager is None:
            return AgentRunResponse(
                run_id="",
                agent_name="recruiter-copilot",
                status=AgentStatus.ERROR,
                error="MCP manager not available",
            )

        summary_workflow = CandidateSummaryWorkflow()
        debrief_workflow = InterviewDebriefWorkflow()
        hiring_workflow = HiringRecommendationWorkflow()

        tasks = [
            summary_workflow.execute(
                candidate_id=candidate_id, mcp_manager=mcp_manager
            ),
            hiring_workflow.execute(
                candidate_id=candidate_id, mcp_manager=mcp_manager
            ),
        ]

        if job_id:
            tasks.append(
                debrief_workflow.execute(
                    candidate_id=candidate_id, job_id=job_id, mcp_manager=mcp_manager
                )
            )

        logger.info(
            "copilot_orchestrating",
            candidate_id=candidate_id,
            workflow_count=len(tasks),
        )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        summary_result: AgentRunResponse | Exception | None = (
            results[0] if len(results) > 0 else None
        )
        hiring_result: AgentRunResponse | Exception | None = (
            results[1] if len(results) > 1 else None
        )
        debrief_result: AgentRunResponse | Exception | None = (
            results[2] if len(results) > 2 else None
        )

        summary_data: dict[str, Any] | None = self._safe_parse(
            summary_result, "candidate_summary"
        )
        hiring_data: dict[str, Any] | None = self._safe_parse(
            hiring_result, "hiring_recommendation"
        )
        debrief_data: dict[str, Any] | None = self._safe_parse(
            debrief_result, "interview_debrief"
        )

        synthesis_input = self._build_synthesis_input(
            summary_data, debrief_data, hiring_data
        )

        registry = get_registry()
        agent = registry.get("recruiter-copilot")
        if not agent:
            return AgentRunResponse(
                run_id="",
                agent_name="recruiter-copilot",
                status=AgentStatus.ERROR,
                error="Recruiter copilot agent not registered",
            )

        logger.info(
            "copilot_synthesizing",
            candidate_id=candidate_id,
        )

        synthesis_response = await agent.run(task=synthesis_input)
        if synthesis_response.status == AgentStatus.ERROR:
            return synthesis_response

        synthesis_data: dict[str, Any] = {}
        if synthesis_response.output:
            try:
                synthesis_data = json.loads(synthesis_response.output)
            except (json.JSONDecodeError, TypeError):
                pass

        output = RecruiterCopilotOutput(
            candidate_id=candidate_id,
            executive_summary=synthesis_data.get("executive_summary", ""),
            candidate_overview=summary_data,
            interview_assessment=debrief_data,
            hiring_recommendation=hiring_data,
            key_strengths=synthesis_data.get("key_strengths", []),
            key_risks=synthesis_data.get("key_risks", []),
            recommended_next_step=synthesis_data.get("recommended_next_step", ""),
        )

        return AgentRunResponse(
            run_id="",
            agent_name="recruiter-copilot",
            status=AgentStatus.COMPLETED,
            output=output.model_dump_json(),
        )

    def _safe_parse(
        self,
        result: AgentRunResponse | Exception | None,
        source: str,
    ) -> dict[str, Any] | None:
        if result is None:
            return None
        if isinstance(result, Exception):
            logger.warning("copilot_sub_workflow_failed", source=source, error=str(result))
            return None
        if result.status == AgentStatus.ERROR:
            logger.warning("copilot_sub_workflow_error", source=source, error=result.error)
            return None
        if not result.output:
            return None
        try:
            return json.loads(result.output)
        except (json.JSONDecodeError, TypeError):
            return None

    def _build_synthesis_input(
        self,
        summary_data: dict[str, Any] | None,
        debrief_data: dict[str, Any] | None,
        hiring_data: dict[str, Any] | None,
    ) -> str:
        lines: list[str] = []

        lines.append("=== CANDIDATE OVERVIEW ===")
        lines.append(
            json.dumps(summary_data, indent=2) if summary_data else "(not available)"
        )

        lines.append("")
        lines.append("=== INTERVIEW ASSESSMENT ===")
        lines.append(
            json.dumps(debrief_data, indent=2) if debrief_data else "(not available)"
        )

        lines.append("")
        lines.append("=== HIRING RECOMMENDATION ===")
        lines.append(
            json.dumps(hiring_data, indent=2) if hiring_data else "(not available)"
        )

        return "\n".join(lines)
