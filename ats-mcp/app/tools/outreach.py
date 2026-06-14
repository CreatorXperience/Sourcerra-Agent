"""
TODO: BACKEND_REQUIRED — Outreach tool adapters.

These tools require backend endpoints that may not yet exist.
Once the backend exposes the corresponding APIs, remove the
TODO markers and implement the actual HTTP calls via BackendClient.

Expected endpoints:
  GET  /ui/emails/:candidateId/emails — list email history
  POST /ui/emails/send — send email
"""

from app.schemas.outreach import ListEmailHistoryResponse, SendEmailResponse


async def ats_get_email_history(
    arguments: dict,
    client=None,
) -> tuple[list[dict], bool]:
    """TODO: BACKEND_REQUIRED — Get email history for a candidate."""
    return [{"type": "text", "text": str(ListEmailHistoryResponse().model_dump(mode="json"))}], False


async def ats_send_email(
    arguments: dict,
    client=None,
) -> tuple[list[dict], bool]:
    """TODO: BACKEND_REQUIRED — Send an email to a candidate."""
    return [{"type": "text", "text": '{"message": "Not yet implemented — backend endpoint required"}'}], True
