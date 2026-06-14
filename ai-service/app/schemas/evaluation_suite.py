from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EvaluationIssue(BaseModel):
    field: str
    message: str
    severity: str


class EvaluationResult(BaseModel):
    evaluator_name: str
    score: float
    passed: bool
    issues: list[EvaluationIssue] = Field(default_factory=list)


class WorkflowEvaluationReport(BaseModel):
    workflow_name: str
    completeness: EvaluationResult
    hallucination: EvaluationResult
    consistency: EvaluationResult
    prompt_regression: EvaluationResult | None = None
    overall_score: float
    passed: bool
    evaluated_at: datetime = Field(default_factory=datetime.now)


class EvaluationRunRequest(BaseModel):
    workflow_name: str | None = None
    fixture_path: str | None = None


class EvaluationSummary(BaseModel):
    total_workflows: int = 0
    passed: int = 0
    failed: int = 0
    average_overall_score: float = 0.0


class EvaluationRunResponse(BaseModel):
    reports: list[WorkflowEvaluationReport] = Field(default_factory=list)
    summary: EvaluationSummary = Field(default_factory=EvaluationSummary)


class EvalFixture(BaseModel):
    workflow_name: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] = Field(default_factory=dict)
    expected_patterns: dict[str, Any] = Field(default_factory=dict)
