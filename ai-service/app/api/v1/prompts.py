from fastapi import APIRouter

from app.prompts.dashboard import get_all_dashboards, get_prompt_dashboard
from app.prompts.experiments import get_experiment_manager
from app.prompts.registry import get_prompt_registry
from app.schemas.common import SuccessResponse
from app.schemas.prompts import (
    CreateExperimentRequest,
    ExperimentConfig,
    PromptDashboard,
    PromptVersion,
    PromptVersionMetrics,
    RegisterPromptRequest,
)

router = APIRouter()


@router.get("/prompts/versions", response_model=list[PromptVersion])
async def list_versions(workflow_name: str | None = None) -> list[PromptVersion]:
    registry = get_prompt_registry()
    return registry.list_versions(workflow_name)


@router.get("/prompts/versions/{workflow_name}", response_model=list[PromptVersion])
async def list_workflow_versions(workflow_name: str) -> list[PromptVersion]:
    registry = get_prompt_registry()
    return registry.list_versions(workflow_name)


@router.post("/prompts/versions", response_model=PromptVersion)
async def register_prompt(request: RegisterPromptRequest) -> PromptVersion:
    registry = get_prompt_registry()
    return registry.register(request.workflow_name, request.content)


@router.post("/prompts/versions/{prompt_id}/activate", response_model=PromptVersion)
async def activate_version(prompt_id: str) -> PromptVersion:
    registry = get_prompt_registry()
    result = registry.activate(prompt_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prompt version not found")
    return result


@router.post("/prompts/versions/{prompt_id}/archive", response_model=PromptVersion)
async def archive_version(prompt_id: str) -> PromptVersion:
    registry = get_prompt_registry()
    result = registry.archive(prompt_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prompt version not found")
    return result


@router.get("/prompts/experiments", response_model=list[ExperimentConfig])
async def list_experiments(workflow_name: str | None = None) -> list[ExperimentConfig]:
    manager = get_experiment_manager()
    return manager.list_experiments(workflow_name)


@router.post("/prompts/experiments", response_model=ExperimentConfig)
async def create_experiment(request: CreateExperimentRequest) -> ExperimentConfig:
    manager = get_experiment_manager()
    return manager.create_experiment(
        workflow_name=request.workflow_name,
        prompt_id_a=request.prompt_id_a,
        prompt_id_b=request.prompt_id_b,
        strategy=request.strategy,
        weight_a=request.weight_a,
    )


@router.post("/prompts/experiments/{experiment_id}/disable", response_model=SuccessResponse)
async def disable_experiment(experiment_id: str) -> SuccessResponse:
    manager = get_experiment_manager()
    if manager.disable_experiment(experiment_id):
        return SuccessResponse(message="Experiment disabled")
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Experiment not found")


@router.get("/prompts/dashboard", response_model=list[PromptDashboard])
async def all_dashboards() -> list[PromptDashboard]:
    return get_all_dashboards()


@router.get("/prompts/dashboard/{workflow_name}", response_model=PromptDashboard)
async def workflow_dashboard(workflow_name: str) -> PromptDashboard:
    return get_prompt_dashboard(workflow_name)


@router.get("/prompts/dashboard/{workflow_name}/best", response_model=PromptVersionMetrics)
async def best_version(workflow_name: str) -> PromptVersionMetrics:
    dashboard = get_prompt_dashboard(workflow_name)
    best = dashboard.best_version()
    if not best:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No version data available")
    return best
