from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PromptStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class RolloutStrategy(str, Enum):
    FULL_A = "full_a"
    SPLIT_50 = "split_50"
    WEIGHTED = "weighted"


class PromptVersion(BaseModel):
    prompt_id: str
    workflow_name: str
    version: int
    status: PromptStatus = PromptStatus.DRAFT
    content: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class RegisterPromptRequest(BaseModel):
    workflow_name: str
    content: str


class ExperimentConfig(BaseModel):
    experiment_id: str
    workflow_name: str
    prompt_id_a: str
    prompt_id_b: str
    strategy: RolloutStrategy = RolloutStrategy.FULL_A
    weight_a: float = 1.0
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


class CreateExperimentRequest(BaseModel):
    workflow_name: str
    prompt_id_a: str
    prompt_id_b: str
    strategy: RolloutStrategy = RolloutStrategy.FULL_A
    weight_a: float = 1.0


class PromptVersionMetrics(BaseModel):
    prompt_id: str
    workflow_name: str
    version: int
    usage_count: int = 0
    approval_rate: float = 0.0
    rejection_rate: float = 0.0
    hallucination_score: float = 0.0
    completeness_score: float = 0.0
    average_evaluation_score: float = 0.0


class PromptDashboard(BaseModel):
    workflow_name: str
    versions: list[PromptVersionMetrics] = Field(default_factory=list)
    active_version: PromptVersionMetrics | None = None

    def best_version(self) -> PromptVersionMetrics | None:
        scored = [v for v in self.versions if v.usage_count > 0]
        if not scored:
            return None
        return max(scored, key=lambda v: v.approval_rate + v.average_evaluation_score)
