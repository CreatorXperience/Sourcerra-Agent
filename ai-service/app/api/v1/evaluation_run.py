from fastapi import APIRouter

from app.evaluation.evaluators.runner import EvaluationRunner
from app.schemas.evaluation_suite import EvaluationRunRequest, EvaluationRunResponse

router = APIRouter()
_runner = EvaluationRunner()


@router.post("/evaluation/run", response_model=EvaluationRunResponse)
async def run_evaluation(request: EvaluationRunRequest) -> EvaluationRunResponse:
    return _runner.run(request)
