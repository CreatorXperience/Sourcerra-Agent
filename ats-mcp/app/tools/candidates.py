import time
from typing import Any

from app.clients import BackendClient, get_backend_client
from app.config.logging import get_logger
from app.core.errors import BackendConnectionError, BackendResponseError, NotFoundError, tool_error_to_content
from app.core.tracing import get_tracer
from app.schemas.candidates import Candidate, GetCandidateRequest, ListCandidatesRequest, ListCandidatesResponse

logger = get_logger(__name__)


async def ats_get_candidate(
    arguments: dict[str, Any],
    client: BackendClient | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    tracer = get_tracer()
    start = time.time()
    client = client or get_backend_client()

    try:
        req = GetCandidateRequest(**arguments)
    except Exception as exc:
        duration = (time.time() - start) * 1000
        tracer.trace_sync("ats_get_candidate", arguments, None, duration, error=str(exc))
        return tool_error_to_content(BackendResponseError(400, str(exc)))

    try:
        raw = await client.get(f"/ui/candidates/{req.candidate_id}")
    except Exception as exc:
        duration = (time.time() - start) * 1000
        tracer.trace_sync("ats_get_candidate", arguments, None, duration, error=str(exc))
        return tool_error_to_content(BackendConnectionError(str(exc)))

    if not raw:
        duration = (time.time() - start) * 1000
        err = NotFoundError("Candidate", req.candidate_id)
        tracer.trace_sync("ats_get_candidate", arguments, None, duration, error=err.message)
        return tool_error_to_content(err)

    candidate = _parse_candidate(raw)
    result = {"candidate": candidate.model_dump(mode="json")}
    duration = (time.time() - start) * 1000
    tracer.trace_sync("ats_get_candidate", arguments, result, duration)
    return [{"type": "text", "text": str(candidate.model_dump(mode="json"))}], False


async def ats_list_candidates(
    arguments: dict[str, Any],
    client: BackendClient | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    tracer = get_tracer()
    start = time.time()
    client = client or get_backend_client()

    try:
        req = ListCandidatesRequest(**arguments)
    except Exception as exc:
        duration = (time.time() - start) * 1000
        tracer.trace_sync("ats_list_candidates", arguments, None, duration, error=str(exc))
        return tool_error_to_content(BackendResponseError(400, str(exc)))

    params: dict[str, Any] = {"limit": req.limit}
    if req.search:
        params["search"] = req.search
    if req.stage:
        params["stage"] = req.stage.value
    if req.job_id:
        params["jobId"] = req.job_id
    if req.recommendation:
        params["recommendation"] = req.recommendation.value

    try:
        raw = await client.get("/ui/candidates", params=params)
    except Exception as exc:
        duration = (time.time() - start) * 1000
        tracer.trace_sync("ats_list_candidates", arguments, None, duration, error=str(exc))
        return tool_error_to_content(BackendConnectionError(str(exc)))

    candidates_data = raw if isinstance(raw, list) else raw.get("data", raw) if isinstance(raw, dict) else []
    candidates = [_parse_candidate(c) for c in candidates_data if isinstance(c, dict)]

    response = ListCandidatesResponse(
        candidates=candidates,
        total=len(candidates),
        limit=req.limit,
    )
    result = response.model_dump(mode="json")
    duration = (time.time() - start) * 1000
    tracer.trace_sync("ats_list_candidates", arguments, result, duration)
    return [{"type": "text", "text": str(result)}], False


def _parse_candidate(raw: dict[str, Any]) -> Candidate:
    return Candidate(
        id=raw.get("id", ""),
        name=raw.get("name"),
        email=raw.get("email"),
        phone=raw.get("phone"),
        location=raw.get("location"),
        skills=_parse_json_list(raw.get("skills")),
        seniority=raw.get("seniority"),
        last_role=raw.get("lastRole"),
        years_of_experience=raw.get("yearsOfExperience"),
        education=raw.get("education"),
        stage=raw.get("stage"),
        source=raw.get("source"),
        overall_score=raw.get("overallScore"),
        job_fit_score=raw.get("jobFitScore"),
        skills_score=raw.get("skillsScore"),
        experience_score=raw.get("experienceScore"),
        top_skills_match=_parse_json_list(raw.get("topSkillsMatch")),
        missing_skills=_parse_json_list(raw.get("missingSkills")),
        strengths=_parse_json_list(raw.get("strengths")),
        weaknesses=_parse_json_list(raw.get("weaknesses")),
        recommendation=raw.get("recommendation"),
        summary=raw.get("summary"),
        resume_url=raw.get("resumeUrl"),
        linkedin_url=raw.get("linkedInUrl"),
        github_url=raw.get("githubUrl"),
        assigned_to_id=raw.get("assignedToId"),
        job_id=raw.get("jobId"),
        company_id=raw.get("companyId"),
        ai_status=raw.get("status"),
        is_top_candidate=raw.get("isTopCandidate", False),
        applied_at=raw.get("appliedAt"),
        created_at=raw.get("createdAt"),
        updated_at=raw.get("updatedAt"),
    )


def _parse_json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []
