from enum import Enum

from pydantic import BaseModel, Field


class ComponentStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DependencyHealth(BaseModel):
    name: str
    status: ComponentStatus
    detail: str | None = None
    latency_ms: float | None = None
    error: str | None = None


class HealthCheckResponse(BaseModel):
    status: ComponentStatus
    version: str = "0.1.0"
    uptime_seconds: float = Field(default_factory=lambda: 0.0)
    dependencies: list[DependencyHealth] = []
