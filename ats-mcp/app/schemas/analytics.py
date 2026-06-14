from pydantic import BaseModel, Field


class FunnelStage(BaseModel):
    stage: str
    count: int = 0
    conversion_rate: float | None = None


class FunnelResponse(BaseModel):
    stages: list[FunnelStage] = Field(default_factory=list)


class HiringSpeedResponse(BaseModel):
    avg_time_to_fill_days: float | None = None
    avg_time_to_hire_days: float | None = None
    total_hires: int = 0


class SourceMetric(BaseModel):
    source: str
    candidates: int = 0
    conversion_rate: float | None = None


class SourceAnalyticsResponse(BaseModel):
    sources: list[SourceMetric] = Field(default_factory=list)


class PipelineHealthStage(BaseModel):
    stage: str
    candidate_count: int = 0
    avg_days_in_stage: float | None = None
    health: str = "unknown"


class PipelineHealthResponse(BaseModel):
    stages: list[PipelineHealthStage] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    total_candidates: int = 0
    total_jobs: int = 0
    total_interviews: int = 0
    total_hires: int = 0
