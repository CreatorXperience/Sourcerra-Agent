from typing import Any

from app.evaluation.evaluators.base import BaseEvaluator, EvaluationIssue, EvaluationResult


REQUIRED_FIELDS: dict[str, list[str]] = {
    "candidate_summary": [
        "candidate_name", "overview", "recruiter_observations",
        "open_action_items", "recommended_next_action",
    ],
    "candidate_matching": [
        "job_id", "job_title", "top_candidates",
    ],
    "outreach_generation": [
        "candidate_id", "job_id", "candidate_name", "job_title",
        "subject", "email_body", "linkedin_message", "short_message",
    ],
    "interview_questions": [
        "candidate_id", "job_id", "job_title",
        "technical_questions", "behavioral_questions",
        "follow_up_questions", "focus_areas",
    ],
    "interview_debrief": [
        "candidate_id", "job_id", "interview_summary",
        "validated_strengths", "identified_concerns",
        "further_evaluation_areas", "overall_assessment",
        "recommended_next_step",
    ],
    "hiring_recommendation": [
        "candidate_id", "candidate_name", "candidate_summary",
        "supporting_evidence", "caution_evidence",
        "risk_factors", "missing_information",
        "recruiter_recommendation", "confidence_level",
    ],
    "recruiter_copilot": [
        "candidate_id", "executive_summary",
        "candidate_overview", "hiring_recommendation",
        "key_strengths", "key_risks", "recommended_next_step",
    ],
}

REQUIRED_NESTED_FIELDS: dict[str, list[str]] = {
    "recruiter_copilot": [
        "executive_summary", "key_strengths", "key_risks", "recommended_next_step",
    ],
}


class CompletenessEvaluator(BaseEvaluator):
    def __init__(self) -> None:
        super().__init__("output_completeness")

    def evaluate(
        self,
        output_data: dict[str, Any],
        input_data: dict[str, Any] | None = None,
    ) -> EvaluationResult:
        issues: list[EvaluationIssue] = []
        total_checks = 0
        passed_checks = 0

        workflow_name = input_data.get("workflow_name", "") if input_data else ""
        required = self._get_required_fields(workflow_name)

        for field in required:
            total_checks += 1
            if field not in output_data:
                issues.append(EvaluationIssue(
                    field=field,
                    message=f"Missing required field: {field}",
                    severity="error",
                ))
                continue

            value = output_data[field]
            if isinstance(value, str) and not value.strip():
                issues.append(EvaluationIssue(
                    field=field,
                    message=f"Empty string in required field: {field}",
                    severity="warning",
                ))
                continue

            if isinstance(value, list) and len(value) == 0:
                issues.append(EvaluationIssue(
                    field=field,
                    message=f"Empty list in field: {field}",
                    severity="warning",
                ))
                continue

            if value is None:
                issues.append(EvaluationIssue(
                    field=field,
                    message=f"None value in required field: {field}",
                    severity="error",
                ))
                continue

            passed_checks += 1

        inner = output_data.get(workflow_name.replace("_", "_assessment"), output_data)
        score = passed_checks / total_checks if total_checks > 0 else 1.0
        passed = score >= 0.8

        return EvaluationResult(
            evaluator_name=self.name,
            score=round(score, 2),
            passed=passed,
            issues=issues,
        )

    def _get_required_fields(self, workflow_name: str) -> list[str]:
        return REQUIRED_FIELDS.get(workflow_name, [])
