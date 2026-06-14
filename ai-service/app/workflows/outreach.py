from typing import Any

from app.agents.registry import get_registry
from app.config.logging import get_logger
from app.mcp.client import MCPClientManager
from app.schemas.agents import AgentRunResponse, AgentStatus
from app.workflows.base import BaseWorkflow

logger = get_logger(__name__)


class OutreachGenerationWorkflow(BaseWorkflow):
    async def execute(
        self,
        candidate_id: str,
        job_id: str,
        mcp_manager: MCPClientManager | None = None,
        **kwargs: Any,
    ) -> AgentRunResponse:
        registry = get_registry()
        agent = registry.get("outreach-specialist")
        if not agent:
            return AgentRunResponse(
                run_id="",
                agent_name="outreach-generation",
                status=AgentStatus.ERROR,
                error="Outreach specialist agent not registered",
            )

        if mcp_manager is None:
            return AgentRunResponse(
                run_id="",
                agent_name="outreach-generation",
                status=AgentStatus.ERROR,
                error="MCP manager not available",
            )

        candidate_raw = None
        job_raw = None
        comments_raw = None

        candidate_result = await mcp_manager.call_tool(
            "ats_get_candidate", {"candidate_id": candidate_id}
        )
        if candidate_result.status.value == "success" and candidate_result.output:
            candidate_raw = candidate_result.output

        job_result = await mcp_manager.call_tool(
            "ats_get_job", {"job_id": job_id}
        )
        if job_result.status.value == "success" and job_result.output:
            job_raw = job_result.output

        comments_result = await mcp_manager.call_tool(
            "ats_get_candidate_comments", {"candidate_id": candidate_id}
        )
        if comments_result.status.value == "success" and comments_result.output:
            comments_raw = comments_result.output

        if not candidate_raw:
            return AgentRunResponse(
                run_id="",
                agent_name="outreach-generation",
                status=AgentStatus.ERROR,
                error=f"Candidate not found: {candidate_id}",
            )

        if not job_raw:
            return AgentRunResponse(
                run_id="",
                agent_name="outreach-generation",
                status=AgentStatus.ERROR,
                error=f"Job not found: {job_id}",
            )

        input_text = self._build_input(candidate_raw, job_raw, comments_raw)

        logger.info(
            "workflow_executing",
            workflow="outreach_generation",
            candidate_id=candidate_id,
            job_id=job_id,
        )

        return await agent.run(task=input_text)

    def _build_input(
        self,
        candidate_raw: list[dict[str, Any]],
        job_raw: list[dict[str, Any]],
        comments_raw: list[dict[str, Any]] | None,
    ) -> str:
        lines: list[str] = []

        lines.append("=== CANDIDATE PROFILE ===")
        candidate_text = self._extract_text(candidate_raw)
        lines.append(candidate_text)

        lines.append("")
        lines.append("=== JOB INFORMATION ===")
        job_text = self._extract_text(job_raw)
        lines.append(job_text)

        lines.append("")
        lines.append("=== RECRUITER COMMENTS ===")
        if comments_raw:
            text = self._extract_text(comments_raw)
            if text:
                lines.append(text)
            else:
                lines.append("(none)")
        else:
            lines.append("(none)")

        return "\n".join(lines)

    def _extract_text(self, raw_list: list[dict[str, Any]]) -> str:
        for item in raw_list:
            text = item.get("text", "")
            if text:
                return text
        return ""
