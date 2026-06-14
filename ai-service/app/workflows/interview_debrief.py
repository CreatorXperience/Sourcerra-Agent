from typing import Any

from app.agents.registry import get_registry
from app.config.logging import get_logger
from app.mcp.client import MCPClientManager
from app.schemas.agents import AgentRunResponse, AgentStatus
from app.workflows.base import BaseWorkflow

logger = get_logger(__name__)


class InterviewDebriefWorkflow(BaseWorkflow):
    async def execute(
        self,
        candidate_id: str,
        job_id: str,
        mcp_manager: MCPClientManager | None = None,
        **kwargs: Any,
    ) -> AgentRunResponse:
        registry = get_registry()
        agent = registry.get("interview-debrief")
        if not agent:
            return AgentRunResponse(
                run_id="",
                agent_name="interview-debrief",
                status=AgentStatus.ERROR,
                error="Interview debrief agent not registered",
            )

        if mcp_manager is None:
            return AgentRunResponse(
                run_id="",
                agent_name="interview-debrief",
                status=AgentStatus.ERROR,
                error="MCP manager not available",
            )

        candidate_raw = None
        job_raw = None
        comments_raw = None
        interviews_raw = None
        feedbacks_raw: list[dict[str, Any]] = []
        signals_raw = None

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

        interviews_result = await mcp_manager.call_tool(
            "ats_get_candidate_interviews", {"candidate_id": candidate_id}
        )
        if interviews_result.status.value == "success" and interviews_result.output:
            interviews_raw = interviews_result.output
            interview_ids = self._extract_interview_ids(interviews_raw)
            for interview_id in interview_ids:
                feedback_result = await mcp_manager.call_tool(
                    "ats_get_interview_feedback", {"interview_id": interview_id}
                )
                if feedback_result.status.value == "success" and feedback_result.output:
                    feedbacks_raw.append({
                        "interview_id": interview_id,
                        "feedback": feedback_result.output,
                    })

        signals_result = await mcp_manager.call_tool(
            "ats_get_candidate_signals", {"candidate_id": candidate_id}
        )
        if signals_result.status.value == "success" and signals_result.output:
            signals_raw = signals_result.output

        if not candidate_raw:
            return AgentRunResponse(
                run_id="",
                agent_name="interview-debrief",
                status=AgentStatus.ERROR,
                error=f"Candidate not found: {candidate_id}",
            )

        if not job_raw:
            return AgentRunResponse(
                run_id="",
                agent_name="interview-debrief",
                status=AgentStatus.ERROR,
                error=f"Job not found: {job_id}",
            )

        input_text = self._build_input(
            candidate_raw, job_raw, comments_raw,
            interviews_raw, feedbacks_raw, signals_raw,
        )

        logger.info(
            "workflow_executing",
            workflow="interview_debrief",
            candidate_id=candidate_id,
            job_id=job_id,
        )

        return await agent.run(task=input_text)

    def _build_input(
        self,
        candidate_raw: list[dict[str, Any]],
        job_raw: list[dict[str, Any]],
        comments_raw: list[dict[str, Any]] | None,
        interviews_raw: list[dict[str, Any]] | None,
        feedbacks_raw: list[dict[str, Any]] | None,
        signals_raw: list[dict[str, Any]] | None,
    ) -> str:
        lines: list[str] = []

        lines.append("=== CANDIDATE PROFILE ===")
        lines.append(self._extract_text(candidate_raw))

        lines.append("")
        lines.append("=== JOB INFORMATION ===")
        lines.append(self._extract_text(job_raw))

        lines.append("")
        lines.append("=== RECRUITER COMMENTS ===")
        if comments_raw:
            text = self._extract_text(comments_raw)
            lines.append(text if text else "(none)")
        else:
            lines.append("(none)")

        lines.append("")
        lines.append("=== INTERVIEW RECORDS ===")
        if interviews_raw:
            text = self._extract_text(interviews_raw)
            lines.append(text if text else "(none)")
        else:
            lines.append("(none)")

        lines.append("")
        lines.append("=== INTERVIEW FEEDBACK ===")
        if feedbacks_raw:
            for fb in feedbacks_raw:
                lines.append(f"--- Interview: {fb.get('interview_id', 'unknown')} ---")
                feedback_text = self._extract_text(fb.get("feedback", []))
                lines.append(feedback_text if feedback_text else "(no feedback content)")
        else:
            lines.append("(none)")

        lines.append("")
        lines.append("=== CANDIDATE SIGNALS ===")
        if signals_raw:
            text = self._extract_text(signals_raw)
            lines.append(text if text else "(none)")
        else:
            lines.append("(none)")

        return "\n".join(lines)

    def _extract_interview_ids(
        self,
        interviews_raw: list[dict[str, Any]],
    ) -> list[str]:
        text = self._extract_text(interviews_raw)
        if not text:
            return []

        import json
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return [item.get("id", "") for item in data if item.get("id")]
            if isinstance(data, dict):
                interview_id = data.get("id")
                if interview_id:
                    return [interview_id]
            return []
        except (json.JSONDecodeError, TypeError):
            return []

    def _extract_text(self, raw_list: list[dict[str, Any]]) -> str:
        for item in raw_list:
            text = item.get("text", "")
            if text:
                return text
        return ""
