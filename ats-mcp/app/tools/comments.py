import time
from typing import Any

from app.clients import BackendClient, get_backend_client
from app.config.logging import get_logger
from app.core.errors import BackendConnectionError, BackendResponseError, tool_error_to_content
from app.core.tracing import get_tracer
from app.schemas.comments import Comment, GetCommentsRequest, ListCommentsResponse

logger = get_logger(__name__)


async def ats_get_candidate_comments(
    arguments: dict[str, Any],
    client: BackendClient | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    tracer = get_tracer()
    start = time.time()
    client = client or get_backend_client()

    try:
        req = GetCommentsRequest(**arguments)
    except Exception as exc:
        duration = (time.time() - start) * 1000
        tracer.trace_sync("ats_get_candidate_comments", arguments, None, duration, error=str(exc))
        return tool_error_to_content(BackendResponseError(400, str(exc)))

    try:
        raw = await client.get(f"/ui/candidates/{req.candidate_id}/comments")
    except Exception as exc:
        duration = (time.time() - start) * 1000
        tracer.trace_sync("ats_get_candidate_comments", arguments, None, duration, error=str(exc))
        return tool_error_to_content(BackendConnectionError(str(exc)))

    comments_data = raw if isinstance(raw, list) else raw.get("data", raw) if isinstance(raw, dict) else []
    comments = [_parse_comment(c) for c in comments_data if isinstance(c, dict)]

    response = ListCommentsResponse(comments=comments, total=len(comments))
    result = response.model_dump(mode="json")
    duration = (time.time() - start) * 1000
    tracer.trace_sync("ats_get_candidate_comments", arguments, result, duration)
    return [{"type": "text", "text": str(result)}], False


def _parse_comment(raw: dict[str, Any]) -> Comment:
    return Comment(
        id=raw.get("id", ""),
        content=raw.get("content", ""),
        author_id=raw.get("authorId", ""),
        candidate_id=raw.get("candidateId", ""),
        created_at=raw.get("createdAt"),
        updated_at=raw.get("updatedAt"),
    )
