from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.observability.metrics import get_metrics

router = APIRouter()


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    metrics_service = get_metrics()
    return metrics_service.render().decode("utf-8")
