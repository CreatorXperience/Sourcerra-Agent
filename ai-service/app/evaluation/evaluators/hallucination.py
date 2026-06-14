import json
import re
from typing import Any

from app.evaluation.evaluators.base import BaseEvaluator, EvaluationIssue, EvaluationResult


class HallucinationEvaluator(BaseEvaluator):
    def __init__(self) -> None:
        super().__init__("hallucination_detection")

    def evaluate(
        self,
        output_data: dict[str, Any],
        input_data: dict[str, Any] | None = None,
    ) -> EvaluationResult:
        issues: list[EvaluationIssue] = []

        if not input_data:
            return EvaluationResult(
                evaluator_name=self.name,
                score=1.0,
                passed=True,
                issues=[EvaluationIssue(
                    field="input", message="No input data provided; skipping hallucination check",
                    severity="warning",
                )],
            )

        input_text = self._flatten_to_text(input_data).lower()
        output_text = self._flatten_to_text(output_data).lower()

        output_tokens = self._extract_terms(output_text)
        input_tokens = self._extract_terms(input_text)

        if not output_tokens:
            return self._pass(1.0)

        missing_terms = output_tokens - input_tokens
        ignored = {"none", "n/a", "unknown", "not available", "", "not provided"}

        unsupported = [t for t in missing_terms if t not in ignored]

        if len(unsupported) > 0 and len(output_tokens) > 0:
            ratio = len(unsupported) / len(output_tokens)
        else:
            ratio = 0.0

        for term in unsupported[:10]:
            issues.append(EvaluationIssue(
                field="output_content",
                message=f"Claim not traceable to input: '{term}'",
                severity="warning" if ratio < 0.3 else "error",
            ))

        score = round(max(0.0, 1.0 - ratio), 2)
        passed = score >= 0.7

        return EvaluationResult(
            evaluator_name=self.name,
            score=score,
            passed=passed,
            issues=issues,
        )

    def _flatten_to_text(self, data: Any, depth: int = 0) -> str:
        if depth > 5:
            return ""
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            return " ".join(self._flatten_to_text(v, depth + 1) for v in data.values())
        if isinstance(data, list):
            return " ".join(self._flatten_to_text(v, depth + 1) for v in data)
        if isinstance(data, (int, float)):
            return str(data)
        return ""

    def _extract_terms(self, text: str) -> set[str]:
        words = re.findall(r"[a-zA-Z]{3,}", text)
        return {w.lower() for w in words}
