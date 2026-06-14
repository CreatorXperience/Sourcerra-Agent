import time
from typing import Any

from app.clients import BackendClient, get_backend_client
from app.config.logging import get_logger
from app.core.errors import BackendConnectionError, BackendResponseError, NotFoundError, tool_error_to_content
from app.core.tracing import get_tracer
from app.schemas.jobs import GetJobRequest, Job, JobRequirement, ListJobsRequest, ListJobsResponse

logger = get_logger(__name__)


async def ats_get_job(
    arguments: dict[str, Any],
    client: BackendClient | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    tracer = get_tracer()
    start = time.time()
    client = client or get_backend_client()

    try:
        req = GetJobRequest(**arguments)
    except Exception as exc:
        duration = (time.time() - start) * 1000
        tracer.trace_sync("ats_get_job", arguments, None, duration, error=str(exc))
        return tool_error_to_content(BackendResponseError(400, str(exc)))

    try:
        raw = await client.get(f"/ui/jobs/job/{req.job_id}")
    except Exception as exc:
        duration = (time.time() - start) * 1000
        tracer.trace_sync("ats_get_job", arguments, None, duration, error=str(exc))
        return tool_error_to_content(BackendConnectionError(str(exc)))

    if not raw:
        duration = (time.time() - start) * 1000
        err = NotFoundError("Job", req.job_id)
        tracer.trace_sync("ats_get_job", arguments, None, duration, error=err.message)
        return tool_error_to_content(err)

    job = _parse_job(raw)
    result = {"job": job.model_dump(mode="json")}
    duration = (time.time() - start) * 1000
    tracer.trace_sync("ats_get_job", arguments, result, duration)
    return [{"type": "text", "text": str(job.model_dump(mode="json"))}], False


async def ats_list_jobs(
    arguments: dict[str, Any],
    client: BackendClient | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    tracer = get_tracer()
    start = time.time()
    client = client or get_backend_client()

    try:
        ListJobsRequest(**arguments)
    except Exception as exc:
        duration = (time.time() - start) * 1000
        tracer.trace_sync("ats_list_jobs", arguments, None, duration, error=str(exc))
        return tool_error_to_content(BackendResponseError(400, str(exc)))

    try:
        raw = await client.get("/ui/jobs")
    except Exception as exc:
        duration = (time.time() - start) * 1000
        tracer.trace_sync("ats_list_jobs", arguments, None, duration, error=str(exc))
        return tool_error_to_content(BackendConnectionError(str(exc)))

    jobs_data = raw if isinstance(raw, list) else raw.get("data", raw) if isinstance(raw, dict) else []
    jobs = [_parse_job(j) for j in jobs_data if isinstance(j, dict)]

    response = ListJobsResponse(jobs=jobs, total=len(jobs))
    result = response.model_dump(mode="json")
    duration = (time.time() - start) * 1000
    tracer.trace_sync("ats_list_jobs", arguments, result, duration)
    return [{"type": "text", "text": str(result)}], False


def _parse_job(raw: dict[str, Any]) -> Job:
    reqs_raw = raw.get("requirements") or raw.get("jobRequirements") or []
    requirements = []
    if isinstance(reqs_raw, list):
        for r in reqs_raw:
            if isinstance(r, dict):
                requirements.append(JobRequirement(
                    label=r.get("label", ""),
                    field_type=r.get("fieldType", ""),
                    required=r.get("required", False),
                    options=r.get("options", []),
                    order=r.get("order", 0),
                ))

    count_data = raw.get("_count") or {}
    candidate_count = count_data.get("candidates", 0) if isinstance(count_data, dict) else 0

    return Job(
        id=raw.get("id", ""),
        title=raw.get("title", ""),
        description=raw.get("description"),
        company_id=raw.get("companyId", ""),
        automation_status=raw.get("automationStatus", False),
        requirements=requirements,
        candidate_count=candidate_count,
        created_at=raw.get("createdAt"),
        updated_at=raw.get("updatedAt"),
    )
