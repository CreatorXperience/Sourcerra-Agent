import time
from typing import Any

from app.clients import BackendClient, get_backend_client
from app.config.logging import get_logger
from app.core.errors import BackendConnectionError, BackendResponseError, tool_error_to_content
from app.core.tracing import get_tracer
from app.schemas.tasks import CandidateTask, CandidateTaskStatus, GetTasksRequest, ListTasksResponse

logger = get_logger(__name__)


async def ats_get_candidate_tasks(
    arguments: dict[str, Any],
    client: BackendClient | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    tracer = get_tracer()
    start = time.time()
    client = client or get_backend_client()

    try:
        req = GetTasksRequest(**arguments)
    except Exception as exc:
        duration = (time.time() - start) * 1000
        tracer.trace_sync("ats_get_candidate_tasks", arguments, None, duration, error=str(exc))
        return tool_error_to_content(BackendResponseError(400, str(exc)))

    try:
        raw = await client.get(f"/ui/tasks/{req.candidate_id}/tasks")
    except Exception as exc:
        duration = (time.time() - start) * 1000
        tracer.trace_sync("ats_get_candidate_tasks", arguments, None, duration, error=str(exc))
        return tool_error_to_content(BackendConnectionError(str(exc)))

    tasks_data = raw if isinstance(raw, list) else raw.get("data", raw) if isinstance(raw, dict) else []
    tasks = [_parse_task(t) for t in tasks_data if isinstance(t, dict)]

    response = ListTasksResponse(tasks=tasks, total=len(tasks))
    result = response.model_dump(mode="json")
    duration = (time.time() - start) * 1000
    tracer.trace_sync("ats_get_candidate_tasks", arguments, result, duration)
    return [{"type": "text", "text": str(result)}], False


def _parse_task(raw: dict[str, Any]) -> CandidateTask:
    return CandidateTask(
        id=raw.get("id", ""),
        candidate_id=raw.get("candidateId", ""),
        recruiter_id=raw.get("recruiterId", ""),
        company_id=raw.get("companyId"),
        title=raw.get("title", ""),
        description=raw.get("description"),
        status=raw.get("status", CandidateTaskStatus.TODO),
        due_date=raw.get("dueDate"),
        color=raw.get("color"),
        label=raw.get("label"),
        completed_at=raw.get("completedAt"),
        created_at=raw.get("createdAt"),
        updated_at=raw.get("updatedAt"),
    )
