from typing import Any

from app.evaluation.evaluators.base import BaseEvaluator, EvaluationIssue, EvaluationResult


VALID_RECOMMENDATIONS: dict[str, set[str]] = {
    "candidate_summary": {"advance", "hold", "schedule", "review", "reject", "pass"},
    "interview_debrief": {
        "move to final interview", "advance to offer", "schedule follow-up interview",
        "gather additional feedback", "hold for review", "do not advance",
    },
    "hiring_recommendation": {
        "strong advance", "advance", "advance with caution",
        "hold for more information", "do not advance",
    },
    "recruiter_copilot": {
        "advance to offer", "move to final interview", "schedule follow-up interview",
        "hold for review", "gather additional information", "do not advance",
    },
}

VALID_CONFIDENCE = {"very high", "high", "moderate", "low", "very low"}


class ConsistencyEvaluator(BaseEvaluator):
    def __init__(self) -> None:
        super().__init__("recommendation_consistency")

    def evaluate(
        self,
        output_data: dict[str, Any],
        input_data: dict[str, Any] | None = None,
    ) -> EvaluationResult:
        issues: list[EvaluationIssue] = []
        checks = 0
        passed_checks = 0

        workflow_name = input_data.get("workflow_name", "") if input_data else ""

        rec_field = self._find_recommendation_field(output_data)
        confidence_field = self._find_confidence_field(output_data)

        # Check recommendation validity
        if rec_field:
            checks += 1
            rec_value = str(output_data.get(rec_field, "")).lower().strip()
            valid_recs = self._get_valid_recommendations(workflow_name)
            if valid_recs and rec_value not in valid_recs:
                issues.append(EvaluationIssue(
                    field=rec_field,
                    message=f"Invalid recommendation: '{rec_value}'. Valid: {valid_recs}",
                    severity="error",
                ))
            else:
                passed_checks += 1

        # Check confidence validity
        if confidence_field:
            checks += 1
            conf_value = str(output_data.get(confidence_field, "")).lower().strip()
            if conf_value not in VALID_CONFIDENCE:
                issues.append(EvaluationIssue(
                    field=confidence_field,
                    message=f"Invalid confidence level: '{conf_value}'. Valid: {VALID_CONFIDENCE}",
                    severity="error",
                ))
            else:
                passed_checks += 1

        # Check evidence alignment
        evidence_positive = self._get_list_field(output_data, "supporting_evidence", "validated_strengths")
        evidence_negative = self._get_list_field(output_data, "caution_evidence", "identified_concerns", "risk_factors")

        if rec_field and (evidence_positive or evidence_negative):
            checks += 1
            rec = str(output_data.get(rec_field, "")).lower().strip()
            positive_count = len(evidence_positive)
            negative_count = len(evidence_negative)

            if positive_count == 0 and negative_count == 0:
                issues.append(EvaluationIssue(
                    field="evidence",
                    message="No evidence provided to support recommendation",
                    severity="warning",
                ))
                passed_checks += 1
            elif "advance" in rec and positive_count == 0:
                issues.append(EvaluationIssue(
                    field="evidence",
                    message="Advance recommendation with zero supporting evidence",
                    severity="warning",
                ))
            elif "do not advance" in rec or "hold" in rec:
                if positive_count > negative_count:
                    issues.append(EvaluationIssue(
                        field="evidence",
                        message=f"Hold/Reject recommendation despite more positive evidence ({positive_count} vs {negative_count})",
                        severity="warning",
                    ))
                else:
                    passed_checks += 1
            elif "advance" in rec and negative_count > positive_count:
                issues.append(EvaluationIssue(
                    field="evidence",
                    message=f"Advance recommendation despite more negative evidence ({negative_count} vs {positive_count})",
                    severity="warning",
                ))
            else:
                passed_checks += 1

        check_candidate_name(output_data, input_data, issues, checks, passed_checks)

        score = passed_checks / checks if checks > 0 else 1.0
        passed = score >= 0.7

        return EvaluationResult(
            evaluator_name=self.name,
            score=round(score, 2),
            passed=passed,
            issues=issues,
        )

    def _find_recommendation_field(self, data: dict[str, Any]) -> str | None:
        for key in ("recommended_next_step", "recruiter_recommendation", "recommended_next_action"):
            if key in data:
                return key
        return None

    def _find_confidence_field(self, data: dict[str, Any]) -> str | None:
        return "confidence_level" if "confidence_level" in data else None

    def _get_valid_recommendations(self, workflow_name: str) -> set[str]:
        for prefix, recs in VALID_RECOMMENDATIONS.items():
            if workflow_name.startswith(prefix) or prefix.startswith(workflow_name):
                return recs
        return set()

    def _get_list_field(self, data: dict[str, Any], *field_names: str) -> list[str]:
        result: list[str] = []
        for name in field_names:
            if name in data and isinstance(data[name], list):
                result.extend(data[name])
        return result


def check_candidate_name(
    output_data: dict[str, Any],
    input_data: dict[str, Any] | None,
    issues: list[EvaluationIssue],
    checks: int,
    passed_checks: int,
) -> None:
    if not input_data:
        return
    name = output_data.get("candidate_name", "")
    if not name:
        return
    input_text = str(input_data).lower()
    if name.lower() not in input_text:
        issues.append(EvaluationIssue(
            field="candidate_name",
            message=f"Candidate name '{name}' not found in input data",
            severity="error",
        ))
