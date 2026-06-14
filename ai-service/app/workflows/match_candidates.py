import json
from typing import Any

from app.agents.registry import get_registry
from app.config.logging import get_logger
from app.mcp.client import MCPClientManager
from app.schemas.agents import AgentRunResponse, AgentStatus
from app.workflows.base import BaseWorkflow

logger = get_logger(__name__)


class MatchCandidatesWorkflow(BaseWorkflow):
    async def execute(
        self,
        job_id: str,
        mcp_manager: MCPClientManager | None = None,
        limit: int = 10,
        **kwargs: Any,
    ) -> AgentRunResponse:
        registry = get_registry()
        agent = registry.get("candidate-matcher")
        if not agent:
            return AgentRunResponse(
                run_id="",
                agent_name="match-candidates-workflow",
                status=AgentStatus.ERROR,
                error="Candidate matcher agent not registered",
            )

        if mcp_manager is None:
            return AgentRunResponse(
                run_id="",
                agent_name="match-candidates-workflow",
                status=AgentStatus.ERROR,
                error="MCP manager not available",
            )

        job_raw = None
        candidates_raw = None

        job_result = await mcp_manager.call_tool(
            "ats_get_job", {"job_id": job_id}
        )
        if job_result.status.value == "success" and job_result.output:
            job_raw = job_result.output

        candidates_result = await mcp_manager.call_tool(
            "ats_list_candidates", {"job_id": job_id, "limit": 200}
        )
        if candidates_result.status.value == "success" and candidates_result.output:
            candidates_raw = candidates_result.output

        if not job_raw:
            return AgentRunResponse(
                run_id="",
                agent_name="match-candidates-workflow",
                status=AgentStatus.ERROR,
                error=f"Job not found: {job_id}",
            )

        input_text = self._build_input(job_raw, candidates_raw, limit)

        logger.info(
            "workflow_executing",
            workflow="match_candidates",
            job_id=job_id,
            limit=limit,
        )

        return await agent.run(task=input_text)

    def _build_input(
        self,
        job_raw: list[dict[str, Any]],
        candidates_raw: list[dict[str, Any]] | None,
        limit: int = 10,
    ) -> str:
        lines: list[str] = []

        job_text = self._extract_text(job_raw)
        lines.append("=== JOB INFORMATION ===")
        lines.append(job_text)
        lines.append("")

        lines.append(f"=== TOP {limit} CANDIDATES (sorted by overall_score DESC) ===")
        if candidates_raw:
            candidates = self._parse_candidates(candidates_raw)
            sorted_candidates = sorted(
                candidates,
                key=lambda c: c.get("overall_score") or 0,
                reverse=True,
            )
            top = sorted_candidates[:limit]
            for i, c in enumerate(top, 1):
                lines.append(f"--- Candidate #{i} ---")
                lines.append(f"ID: {c.get('id', '')}")
                lines.append(f"Name: {c.get('name', 'Unknown')}")
                lines.append(f"Overall Score: {c.get('overall_score', 'N/A')}")
                lines.append(f"Job Fit Score: {c.get('job_fit_score', 'N/A')}")
                lines.append(f"Skills Score: {c.get('skills_score', 'N/A')}")
                lines.append(f"Experience Score: {c.get('experience_score', 'N/A')}")
                lines.append(f"Recommendation: {c.get('recommendation', 'N/A')}")
                lines.append(f"Skills: {', '.join(c.get('skills', []))}")
                lines.append(f"Top Skills Match: {', '.join(c.get('top_skills_match', []))}")
                lines.append(f"Missing Skills: {', '.join(c.get('missing_skills', []))}")
                lines.append(f"Strengths: {', '.join(c.get('strengths', []))}")
                lines.append(f"Weaknesses: {', '.join(c.get('weaknesses', []))}")
                lines.append(f"Stage: {c.get('stage', 'N/A')}")
                lines.append("")
        else:
            lines.append("(no candidates found)")
            lines.append("")

        return "\n".join(lines)

    def _extract_text(self, raw_list: list[dict[str, Any]]) -> str:
        for item in raw_list:
            text = item.get("text", "")
            if text:
                return text
        return ""

    def _parse_candidates(self, raw_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        text = self._extract_text(raw_list)
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return []

        if isinstance(parsed, dict):
            candidates = parsed.get("candidates", [])
            if isinstance(candidates, list):
                return candidates
        elif isinstance(parsed, list):
            return parsed
        return []
