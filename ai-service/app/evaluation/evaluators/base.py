from abc import ABC, abstractmethod
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


class BaseEvaluator(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def evaluate(self, output_data: dict[str, Any], input_data: dict[str, Any] | None = None) -> EvaluationResult:
        ...

    def _pass(self, score: float = 1.0) -> EvaluationResult:
        return EvaluationResult(evaluator_name=self.name, score=score, passed=True)

    def _fail(self, score: float, issues: list[EvaluationIssue]) -> EvaluationResult:
        return EvaluationResult(evaluator_name=self.name, score=score, passed=False, issues=issues)
