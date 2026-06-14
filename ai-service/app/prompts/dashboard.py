from app.config.logging import get_logger
from app.evaluation.store import get_feedback_store
from app.prompts.registry import get_prompt_registry
from app.schemas.evaluation import FeedbackRating
from app.schemas.prompts import PromptDashboard, PromptVersionMetrics

logger = get_logger(__name__)


def get_prompt_dashboard(workflow_name: str) -> PromptDashboard:
    registry = get_prompt_registry()
    feedback_store = get_feedback_store()

    versions = registry.list_versions(workflow_name)
    all_feedback = feedback_store.get_feedback_by_workflow(workflow_name)
    all_traces = _get_traces_for_workflow(workflow_name)

    metrics_list: list[PromptVersionMetrics] = []
    for v in versions:
        v_feedback = [f for f in all_feedback if f.prompt_template == v.prompt_id]
        v_traces = [t for t in all_traces if t.prompt_id == v.prompt_id]

        usage = len(v_traces)
        approvals = sum(1 for f in v_feedback if f.rating == FeedbackRating.UP)
        rejections = sum(1 for f in v_feedback if f.rating == FeedbackRating.DOWN)
        total_fb = len(v_feedback)
        approval_rate = round(approvals / total_fb * 100, 1) if total_fb > 0 else 0.0
        rejection_rate = round(rejections / total_fb * 100, 1) if total_fb > 0 else 0.0

        metrics = PromptVersionMetrics(
            prompt_id=v.prompt_id,
            workflow_name=workflow_name,
            version=v.version,
            usage_count=usage,
            approval_rate=approval_rate,
            rejection_rate=rejection_rate,
        )
        metrics_list.append(metrics)

    active = registry.get_active(workflow_name)
    active_metrics = None
    if active:
        for m in metrics_list:
            if m.prompt_id == active.prompt_id:
                active_metrics = m
                break

    return PromptDashboard(
        workflow_name=workflow_name,
        versions=metrics_list,
        active_version=active_metrics,
    )


def get_all_dashboards() -> list[PromptDashboard]:
    registry = get_prompt_registry()
    workflows = set(v.workflow_name for v in registry.list_versions())
    return [get_prompt_dashboard(wf) for wf in sorted(workflows)]


def _get_traces_for_workflow(workflow_name: str) -> list:
    from app.evaluation.tracing import get_tracer_store
    return get_tracer_store().get_traces_by_workflow(workflow_name)
