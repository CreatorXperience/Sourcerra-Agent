from typing import Any

from app.agents.registry import get_registry
from app.config.logging import get_logger
from app.mcp.client import MCPClientManager
from app.schemas.agents import AgentRunResponse, AgentStatus
from app.workflows.base import BaseWorkflow

logger = get_logger(__name__)


class HiringRecommendationWorkflow(BaseWorkflow):
    async def execute(
        self,
        candidate_id: str,
        mcp_manager: MCPClientManager | None = None,
        **kwargs: Any,
    ) -> AgentRunResponse:
        registry = get_registry()
        agent = registry.get("hiring-recommendation")
        if not agent:
            return AgentRunResponse(
                run_id="",
                agent_name="hiring-recommendation",
                status=AgentStatus.ERROR,
                error="Hiring recommendation agent not registered",
            )

        if mcp_manager is None:
            return AgentRunResponse(
                run_id="",
                agent_name="hiring-recommendation",
                status=AgentStatus.ERROR,
                error="MCP manager not available",
            )

        candidate_raw = None
        comments_raw = None
        tasks_raw = None
        timeline_raw = None
        communication_raw = None
        interviews_raw = None
        signals_raw = None

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

        timeline_result = await mcp_manager.call_tool(
            "ats_get_candidate_timeline", {"candidate_id": candidate_id}
        )
        if timeline_result.status.value == "success" and timeline_result.output:
            timeline_raw = timeline_result.output

        communication_result = await mcp_manager.call_tool(
            "ats_get_candidate_communication", {"candidate_id": candidate_id}
        )
        if communication_result.status.value == "success" and communication_result.output:
            communication_raw = communication_result.output

        interviews_result = await mcp_manager.call_tool(
            "ats_get_candidate_interviews", {"candidate_id": candidate_id}
        )
        if interviews_result.status.value == "success" and interviews_result.output:
            interviews_raw = interviews_result.output

        signals_result = await mcp_manager.call_tool(
            "ats_get_candidate_signals", {"candidate_id": candidate_id}
        )
        if signals_result.status.value == "success" and signals_result.output:
            signals_raw = signals_result.output

        if not candidate_raw:
            return AgentRunResponse(
                run_id="",
                agent_name="hiring-recommendation",
                status=AgentStatus.ERROR,
                error=f"Candidate not found: {candidate_id}",
            )

        input_text = self._build_input(
            candidate_raw, comments_raw, tasks_raw,
            timeline_raw, communication_raw, interviews_raw,
            signals_raw,
        )

        logger.info(
            "workflow_executing",
            workflow="hiring_recommendation",
            candidate_id=candidate_id,
        )

        return await agent.run(task=input_text)

    def _build_input(
        self,
        candidate_raw: list[dict[str, Any]],
        comments_raw: list[dict[str, Any]] | None,
        tasks_raw: list[dict[str, Any]] | None,
        timeline_raw: list[dict[str, Any]] | None,
        communication_raw: list[dict[str, Any]] | None,
        interviews_raw: list[dict[str, Any]] | None,
        signals_raw: list[dict[str, Any]] | None,
    ) -> str:
        lines: list[str] = []

        lines.append("=== CANDIDATE PROFILE ===")
        lines.append(self._extract_text(candidate_raw))

        lines.append("")
        lines.append("=== RECRUITER COMMENTS ===")
        lines.append(self._optional_text(comments_raw))

        lines.append("")
        lines.append("=== CANDIDATE TASKS ===")
        lines.append(self._optional_text(tasks_raw))

        lines.append("")
        lines.append("=== CANDIDATE TIMELINE ===")
        lines.append(self._optional_text(timeline_raw))

        lines.append("")
        lines.append("=== CANDIDATE COMMUNICATION ===")
        lines.append(self._optional_text(communication_raw))

        lines.append("")
        lines.append("=== CANDIDATE INTERVIEWS ===")
        lines.append(self._optional_text(interviews_raw))

        lines.append("")
        lines.append("=== CANDIDATE SIGNALS ===")
        lines.append(self._optional_text(signals_raw))

        return "\n".join(lines)

    def _optional_text(self, raw: list[dict[str, Any]] | None) -> str:
        if raw:
            text = self._extract_text(raw)
            return text if text else "(none)"
        return "(none)"

    def _extract_text(self, raw_list: list[dict[str, Any]]) -> str:
        for item in raw_list:
            text = item.get("text", "")
            if text:
                return text
        return ""
