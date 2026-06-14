from fastapi import APIRouter

from app.evaluation.store import get_feedback_store
from app.schemas.evaluation import FeedbackRequest, FeedbackRecord, FeedbackStats
from app.schemas.common import SuccessResponse

router = APIRouter()


@router.post("/feedback", response_model=FeedbackRecord)
async def submit_feedback(request: FeedbackRequest) -> FeedbackRecord:
    store = get_feedback_store()
    record = store.add_feedback(
        workflow_name=request.workflow_name,
        candidate_id=request.candidate_id,
        rating=request.rating,
        feedback_text=request.feedback_text,
    )
    return record


@router.get("/feedback", response_model=list[FeedbackRecord])
async def list_feedback(
    workflow_name: str | None = None,
    candidate_id: str | None = None,
) -> list[FeedbackRecord]:
    store = get_feedback_store()
    if workflow_name and candidate_id:
        all_records = store.get_feedback_by_workflow(workflow_name)
        return [r for r in all_records if r.candidate_id == candidate_id]
    if workflow_name:
        return store.get_feedback_by_workflow(workflow_name)
    if candidate_id:
        return store.get_feedback_by_candidate(candidate_id)
    return store.get_all_feedback()


@router.get("/feedback/stats", response_model=FeedbackStats)
async def feedback_stats() -> FeedbackStats:
    store = get_feedback_store()
    return store.get_stats()


@router.get("/feedback/health", response_model=SuccessResponse)
async def feedback_health() -> SuccessResponse:
    store = get_feedback_store()
    return SuccessResponse(
        message="Evaluation system operational",
        data={"total_feedback": len(store.get_all_feedback())},
    )
