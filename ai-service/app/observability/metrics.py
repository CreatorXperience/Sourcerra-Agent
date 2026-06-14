import time
from typing import Any

from app.config.logging import get_logger

logger = get_logger(__name__)

try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    def generate_latest() -> bytes:
        return b""


class MetricsService:
    def __init__(self) -> None:
        if not PROMETHEUS_AVAILABLE:
            logger.info("metrics_disabled", reason="prometheus_client not installed")
            return

        self._workflow_executions = Counter(
            "workflow_executions_total",
            "Total workflow executions",
            ["workflow", "status"],
        )
        self._workflow_latency = Histogram(
            "workflow_execution_duration_seconds",
            "Workflow execution latency",
            ["workflow"],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
        )
        self._agent_executions = Counter(
            "agent_executions_total",
            "Total agent executions",
            ["agent", "status"],
        )
        self._agent_latency = Histogram(
            "agent_execution_duration_seconds",
            "Agent execution latency",
            ["agent"],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
        )
        self._llm_calls = Counter(
            "llm_calls_total",
            "Total LLM calls",
            ["model", "provider"],
        )
        self._token_usage = Counter(
            "llm_token_usage_total",
            "Token usage",
            ["model", "type"],
        )
        self._error_rate = Counter(
            "error_rate_total",
            "Error rate",
            ["workflow", "error_type"],
        )
        self._active_workflows = Gauge(
            "active_workflows",
            "Currently active workflows",
            ["workflow"],
        )

    def track_workflow(
        self, workflow: str, status: str, duration_ms: float
    ) -> None:
        if not PROMETHEUS_AVAILABLE:
            return
        self._workflow_executions.labels(workflow=workflow, status=status).inc()
        self._workflow_latency.labels(workflow=workflow).observe(duration_ms / 1000.0)

    def track_agent(
        self, agent: str, status: str, duration_ms: float
    ) -> None:
        if not PROMETHEUS_AVAILABLE:
            return
        self._agent_executions.labels(agent=agent, status=status).inc()
        self._agent_latency.labels(agent=agent).observe(duration_ms / 1000.0)

    def track_llm_call(
        self, model: str, provider: str, prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> None:
        if not PROMETHEUS_AVAILABLE:
            return
        self._llm_calls.labels(model=model, provider=provider).inc()
        if prompt_tokens:
            self._token_usage.labels(model=model, type="prompt").inc(prompt_tokens)
        if completion_tokens:
            self._token_usage.labels(model=model, type="completion").inc(completion_tokens)

    def track_error(self, workflow: str, error_type: str) -> None:
        if not PROMETHEUS_AVAILABLE:
            return
        self._error_rate.labels(workflow=workflow, error_type=error_type).inc()

    def set_active_workflow(self, workflow: str, count: int = 1) -> None:
        if not PROMETHEUS_AVAILABLE:
            return
        self._active_workflows.labels(workflow=workflow).set(count)

    def render(self) -> bytes:
        if not PROMETHEUS_AVAILABLE:
            return b"# Metrics disabled: install prometheus_client\n"
        return generate_latest()


_metrics: MetricsService | None = None


def get_metrics() -> MetricsService:
    global _metrics
    if _metrics is None:
        _metrics = MetricsService()
    return _metrics
