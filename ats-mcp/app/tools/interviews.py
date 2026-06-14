"""
TODO: BACKEND_REQUIRED — Interview tool adapters.

These tools require backend endpoints that may not yet exist.
Once the backend exposes the corresponding APIs, remove the
TODO markers and implement the actual HTTP calls via BackendClient.

Expected endpoints:
  GET  /interviews — list interviews
  GET  /interviews/:id — get single interview
  POST /interviews — schedule interview
  POST /interviews/:id/reschedule — reschedule
  POST /interviews/:id/cancel — cancel
  POST /interviews/:id/complete — mark complete
"""

from app.schemas.interviews import ListInterviewsResponse


async def ats_list_interviews(
    arguments: dict,
    client=None,
) -> tuple[list[dict], bool]:
    """TODO: BACKEND_REQUIRED — List interviews with filters."""
    return [{"type": "text", "text": str(ListInterviewsResponse().model_dump(mode="json"))}], False


async def ats_get_interview(
    arguments: dict,
    client=None,
) -> tuple[list[dict], bool]:
    """TODO: BACKEND_REQUIRED — Get interview details."""
    return [{"type": "text", "text": '{"message": "Not yet implemented — backend endpoint required"}'}], True


async def ats_schedule_interview(
    arguments: dict,
    client=None,
) -> tuple[list[dict], bool]:
    """TODO: BACKEND_REQUIRED — Schedule a new interview."""
    return [{"type": "text", "text": '{"message": "Not yet implemented — backend endpoint required"}'}], True


async def ats_reschedule_interview(
    arguments: dict,
    client=None,
) -> tuple[list[dict], bool]:
    """TODO: BACKEND_REQUIRED — Reschedule an existing interview."""
    return [{"type": "text", "text": '{"message": "Not yet implemented — backend endpoint required"}'}], True


async def ats_cancel_interview(
    arguments: dict,
    client=None,
) -> tuple[list[dict], bool]:
    """TODO: BACKEND_REQUIRED — Cancel an interview."""
    return [{"type": "text", "text": '{"message": "Not yet implemented — backend endpoint required"}'}], True


async def ats_complete_interview(
    arguments: dict,
    client=None,
) -> tuple[list[dict], bool]:
    """TODO: BACKEND_REQUIRED — Mark interview as completed."""
    return [{"type": "text", "text": '{"message": "Not yet implemented — backend endpoint required"}'}], True
