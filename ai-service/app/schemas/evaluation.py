from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FeedbackRating(str, Enum):
    UP = "up"
    DOWN = "down"


class FeedbackRequest(BaseModel):
    workflow_name: str
    candidate_id: str
    rating: FeedbackRating
    feedback_text: str = ""


class FeedbackRecord(BaseModel):
    id: str
    workflow_name: str
    candidate_id: str
    rating: FeedbackRating
    feedback_text: str
    timestamp: datetime
    prompt_template: str = ""
    model_used: str = ""


class WorkflowTrace(BaseModel):
    run_id: str
    workflow_name: str
    candidate_id: str
    prompt_template: str
    model_used: str
    prompt_id: str = ""
    prompt_version: int = 0
    output_snapshot: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None


class WorkflowMetrics(BaseModel):
    workflow_name: str
    total: int = 0
    approvals: int = 0
    rejections: int = 0
    approval_rate: float = 0.0
    average_confidence: float = 0.0


class FeedbackStats(BaseModel):
    total_feedback: int = 0
    approval_rate: float = 0.0
    rejection_rate: float = 0.0
    workflow_usage: dict[str, int] = Field(default_factory=dict)
    workflow_metrics: list[WorkflowMetrics] = Field(default_factory=list)
