import json
from pathlib import Path
from typing import Any

from app.evaluation.evaluators.base import BaseEvaluator, EvaluationIssue, EvaluationResult
from app.evaluation.evaluators.completeness import REQUIRED_FIELDS


FIXTURES_DIR = Path(__file__).parent.parent.parent.parent / "data" / "fixtures"


class PromptRegressionEvaluator(BaseEvaluator):
    def __init__(self, fixture_path: str | None = None) -> None:
        super().__init__("prompt_regression")
        self._fixture_path = Path(fixture_path) if fixture_path else FIXTURES_DIR

    def evaluate(
        self,
        output_data: dict[str, Any],
        input_data: dict[str, Any] | None = None,
    ) -> EvaluationResult:
        issues: list[EvaluationIssue] = []
        workflow_name = input_data.get("workflow_name", "") if input_data else ""

        fixtures = self._load_fixtures(workflow_name)
        if not fixtures:
            return EvaluationResult(
                evaluator_name=self.name,
                score=1.0,
                passed=True,
                issues=[EvaluationIssue(
                    field="fixtures",
                    message=f"No regression fixtures found for '{workflow_name}'; skipping",
                    severity="warning",
                )],
            )

        total_checks = 0
        passed_checks = 0

        for fixture in fixtures:
            expected = fixture.get("output_data", {})

            all_keys = set(list(expected.keys()) + list(output_data.keys()))
            for key in all_keys:
                total_checks += 1
                if key in expected and key in output_data:
                    expected_val = expected[key]
                    actual_val = output_data[key]
                    if isinstance(expected_val, str) and isinstance(actual_val, str):
                        if not self._text_matches(expected_val, actual_val):
                            issues.append(EvaluationIssue(
                                field=key,
                                message=f"Format regression for '{key}': expected '{expected_val[:50]}...', got '{actual_val[:50]}...'",
                                severity="warning",
                            ))
                        else:
                            passed_checks += 1
                    elif isinstance(expected_val, list) and isinstance(actual_val, list):
                        if len(actual_val) >= len(expected_val) * 0.5:
                            passed_checks += 1
                        else:
                            issues.append(EvaluationIssue(
                                field=key,
                                message=f"List length regression for '{key}': expected ~{len(expected_val)}, got {len(actual_val)}",
                                severity="warning",
                            ))
                    elif type(expected_val) == type(actual_val):
                        passed_checks += 1
                    else:
                        issues.append(EvaluationIssue(
                            field=key,
                            message=f"Type regression for '{key}': expected {type(expected_val).__name__}, got {type(actual_val).__name__}",
                            severity="error",
                        ))
                elif key in expected and key not in output_data:
                    issues.append(EvaluationIssue(
                        field=key,
                        message=f"Missing field '{key}' that was present in fixture",
                        severity="error",
                    ))
                else:
                    passed_checks += 1

        score = passed_checks / total_checks if total_checks > 0 else 1.0
        passed = score >= 0.8

        return EvaluationResult(
            evaluator_name=self.name,
            score=round(score, 2),
            passed=passed,
            issues=issues,
        )

    def _load_fixtures(self, workflow_name: str) -> list[dict[str, Any]]:
        if not self._fixture_path.exists():
            return []
        fixtures: list[dict[str, Any]] = []
        pattern = f"{workflow_name}*.json"
        for f in sorted(self._fixture_path.glob(pattern)):
            try:
                data = json.loads(f.read_text())
                fixtures.append(data)
            except (json.JSONDecodeError, OSError):
                continue
        return fixtures

    def _text_matches(self, expected: str, actual: str) -> bool:
        e = expected.lower().strip()
        a = actual.lower().strip()
        if len(e) < 20:
            return e == a
        return len(e) * 0.5 <= len(a) <= len(e) * 2.0
