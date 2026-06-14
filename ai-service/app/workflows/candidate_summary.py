from typing import Any

from app.agents.registry import get_registry
from app.config.logging import get_logger
from app.mcp.client import MCPClientManager
from app.schemas.agents import AgentRunResponse, AgentStatus
from app.workflows.base import BaseWorkflow

logger = get_logger(__name__)


class CandidateSummaryWorkflow(BaseWorkflow):
    async def execute(
        self,
        candidate_id: str,
        mcp_manager: MCPClientManager | None = None,
        **kwargs: Any,
    ) -> AgentRunResponse:
        registry = get_registry()
        agent = registry.get("candidate-summarizer")
        if not agent:
            return AgentRunResponse(
                run_id="",
                agent_name="candidate-summary",
                status=AgentStatus.ERROR,
                error="Candidate summarizer agent not registered",
            )

        if mcp_manager is None:
            return AgentRunResponse(
                run_id="",
                agent_name="candidate-summary",
                status=AgentStatus.ERROR,
                error="MCP manager not available",
            )

        candidate_raw = None
        comments_raw = None
        tasks_raw = None

        candidate_result = await mcp_manager.call_tool(
            "ats_get_candidate", {"candidate_id": candidate_id}
        )
        if candidate_result.status.value == "success" and candidate_result.output:
            candidate_raw = candidate_result.output

        comments_result = await mcp_manager.call_tool(
            "ats_get_candidate_comments", {"candidate_id": candidate_id}
        )
        if comments_result.status.value == "success" and comments_result.output:
            comments_raw = comments_result.output

        tasks_result = await mcp_manager.call_tool(
            "ats_get_candidate_tasks", {"candidate_id": candidate_id}
        )
        if tasks_result.status.value == "success" and tasks_result.output:
            tasks_raw = tasks_result.output

        input_text = self._build_input(candidate_raw, comments_raw, tasks_raw)

        logger.info(
            "workflow_executing",
            workflow="candidate_summary",
            candidate_id=candidate_id,
        )

        return await agent.run(task=input_text)

    def _build_input(
        self,
        candidate_raw: list[dict[str, Any]] | None,
        comments_raw: list[dict[str, Any]] | None,
        tasks_raw: list[dict[str, Any]] | None,
    ) -> str:
        lines: list[str] = []

        lines.append("=== CANDIDATE PROFILE ===")
        if candidate_raw:
            for item in candidate_raw:
                text = item.get("text", "")
                if text:
                    lines.append(text)
        else:
            lines.append("(not available)")

        lines.append("")
        lines.append("=== RECRUITER COMMENTS ===")
        if comments_raw:
            for item in comments_raw:
                text = item.get("text", "")
                if text:
                    lines.append(text)
        else:
            lines.append("(none)")

        lines.append("")
        lines.append("=== CANDIDATE TASKS ===")
        if tasks_raw:
            for item in tasks_raw:
                text = item.get("text", "")
                if text:
                    lines.append(text)
        else:
            lines.append("(none)")

        return "\n".join(lines)
