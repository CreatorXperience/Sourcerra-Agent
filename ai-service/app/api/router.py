from fastapi import APIRouter

from app.api.v1.ats import router as ats_router
from app.api.v1.evaluation import router as evaluation_router
from app.api.v1.evaluation_run import router as evaluation_run_router
from app.api.v1.health import router as health_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.prompts import router as prompts_router
from app.api.v1.tools import router as tools_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(metrics_router, prefix="", tags=["Metrics"])
api_router.include_router(ats_router, prefix="", tags=["ATS"])
api_router.include_router(evaluation_router, prefix="", tags=["Evaluation"])
api_router.include_router(evaluation_run_router, prefix="", tags=["Evaluation"])
api_router.include_router(prompts_router, prefix="", tags=["Prompts"])
api_router.include_router(tools_router, prefix="/tools", tags=["Tools"])
