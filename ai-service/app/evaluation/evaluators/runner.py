from typing import Any

from app.evaluation.evaluators.completeness import CompletenessEvaluator
from app.evaluation.evaluators.consistency import ConsistencyEvaluator
from app.evaluation.evaluators.hallucination import HallucinationEvaluator
from app.evaluation.evaluators.prompt_regression import PromptRegressionEvaluator
from app.schemas.evaluation_suite import (
    EvaluationIssue,
    EvaluationResult,
    EvaluationRunRequest,
    EvaluationRunResponse,
    EvaluationSummary,
    WorkflowEvaluationReport,
)


ALL_WORKFLOWS = [
    "candidate_summary",
    "candidate_matching",
    "outreach_generation",
    "interview_questions",
    "interview_debrief",
    "hiring_recommendation",
    "recruiter_copilot",
]


class EvaluationRunner:
    def __init__(self) -> None:
        self._completeness = CompletenessEvaluator()
        self._hallucination = HallucinationEvaluator()
        self._consistency = ConsistencyEvaluator()
        self._regression = PromptRegressionEvaluator()

    def run(self, request: EvaluationRunRequest) -> EvaluationRunResponse:
        workflows = [request.workflow_name] if request.workflow_name else ALL_WORKFLOWS

        reports: list[WorkflowEvaluationReport] = []
        total_score = 0.0
        passed_count = 0

        for wf in workflows:
            report = self._evaluate_workflow(wf, request)
            reports.append(report)
            total_score += report.overall_score
            if report.passed:
                passed_count += 1

        avg_score = round(total_score / len(reports), 2) if reports else 0.0

        return EvaluationRunResponse(
            reports=reports,
            summary=EvaluationSummary(
                total_workflows=len(reports),
                passed=passed_count,
                failed=len(reports) - passed_count,
                average_overall_score=avg_score,
            ),
        )

    def _evaluate_workflow(
        self,
        workflow_name: str,
        request: EvaluationRunRequest,
    ) -> WorkflowEvaluationReport:
        input_data: dict[str, Any] = {"workflow_name": workflow_name}
        output_data: dict[str, Any] = self._load_fixture_output(workflow_name, request.fixture_path)

        completeness = self._to_result(self._completeness.evaluate(output_data, input_data))
        hallucination = self._to_result(self._hallucination.evaluate(output_data, input_data))
        consistency = self._to_result(self._consistency.evaluate(output_data, input_data))
        regression = self._to_result(self._regression.evaluate(output_data, input_data))

        scores = [
            completeness.score,
            hallucination.score,
            consistency.score,
            regression.score if regression.passed else 0.0,
        ]
        overall = round(sum(scores) / len(scores), 2)
        overall_passed = overall >= 0.7

        return WorkflowEvaluationReport(
            workflow_name=workflow_name,
            completeness=completeness,
            hallucination=hallucination,
            consistency=consistency,
            prompt_regression=regression,
            overall_score=overall,
            passed=overall_passed,
        )

    @staticmethod
    def _to_result(result: Any) -> EvaluationResult:
        return EvaluationResult(
            evaluator_name=result.evaluator_name,
            score=result.score,
            passed=result.passed,
            issues=[
                EvaluationIssue(field=i.field, message=i.message, severity=i.severity)
                for i in result.issues
            ],
        )

    def _load_fixture_output(
        self,
        workflow_name: str,
        fixture_path: str | None = None,
    ) -> dict[str, Any]:
        from app.evaluation.evaluators.prompt_regression import FIXTURES_DIR
        base = fixture_path if fixture_path else FIXTURES_DIR
        from pathlib import Path
        import json

        p = Path(base)
        if not p.exists():
            return {}

        candidates = list(p.glob(f"{workflow_name}*.json"))
        if not candidates:
            return {}

        try:
            data = json.loads(candidates[0].read_text())
            return data.get("output_data", {})
        except (json.JSONDecodeError, OSError):
            return {}
