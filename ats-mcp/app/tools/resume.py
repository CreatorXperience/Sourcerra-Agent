"""
TODO: BACKEND_REQUIRED — Resume processing tool adapters.

These tools require backend endpoints that may not yet exist.
Once the backend exposes the corresponding APIs, remove the
TODO markers and implement the actual HTTP calls via BackendClient.

Expected endpoints:
  GET  /n8n/processing/:candidateId — get processing status
  POST /n8n/processing/:candidateId/retry — retry processing
"""

from app.schemas.resume import ProcessingStatusResponse, RetryProcessingResponse


async def ats_get_resume_processing_status(
    arguments: dict,
    client=None,
) -> tuple[list[dict], bool]:
    """TODO: BACKEND_REQUIRED — Get AI processing status for a candidate's resume."""
    return [{"type": "text", "text": str(ProcessingStatusResponse(candidate_id=arguments.get("candidate_id", "")))}], False


async def ats_retry_resume_processing(
    arguments: dict,
    client=None,
) -> tuple[list[dict], bool]:
    """TODO: BACKEND_REQUIRED — Retry failed resume processing."""
    return [{"type": "text", "text": '{"message": "Not yet implemented — backend endpoint required"}'}], True
