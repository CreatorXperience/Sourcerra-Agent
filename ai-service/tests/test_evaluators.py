import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.evaluation.evaluators.base import BaseEvaluator, EvaluationIssue, EvaluationResult
from app.evaluation.evaluators.completeness import CompletenessEvaluator
from app.evaluation.evaluators.consistency import ConsistencyEvaluator
from app.evaluation.evaluators.hallucination import HallucinationEvaluator
from app.evaluation.evaluators.prompt_regression import PromptRegressionEvaluator
from app.evaluation.evaluators.runner import EvaluationRunner
from app.schemas.evaluation_suite import EvaluationRunRequest, EvaluationRunResponse


class TestBaseEvaluator:
    def test_pass_result(self) -> None:
        class DummyEvaluator(BaseEvaluator):
            def evaluate(self, output_data, input_data=None):
                return self._pass(1.0)

        e = DummyEvaluator("test")
        result = e.evaluate({})
        assert result.score == 1.0
        assert result.passed is True
        assert result.evaluator_name == "test"

    def test_fail_result(self) -> None:
        class DummyEvaluator(BaseEvaluator):
            def evaluate(self, output_data, input_data=None):
                return self._fail(0.0, [EvaluationIssue(field="f", message="fail", severity="error")])

        e = DummyEvaluator("test")
        result = e.evaluate({})
        assert result.score == 0.0
        assert result.passed is False
        assert len(result.issues) == 1


class TestCompletenessEvaluator:
    def test_complete_output(self) -> None:
        evaluator = CompletenessEvaluator()
        output = {
            "candidate_name": "Alice",
            "overview": "Great candidate",
            "recruiter_observations": ["Good comms"],
            "open_action_items": ["Schedule"],
            "recommended_next_action": "Advance",
        }
        result = evaluator.evaluate(output, {"workflow_name": "candidate_summary"})
        assert result.passed is True
        assert result.score >= 0.8

    def test_missing_fields(self) -> None:
        evaluator = CompletenessEvaluator()
        result = evaluator.evaluate({"candidate_name": "Alice"}, {"workflow_name": "candidate_summary"})
        assert result.passed is False
        assert any("Missing required field" in i.message for i in result.issues)

    def test_empty_string_field(self) -> None:
        evaluator = CompletenessEvaluator()
        output = {
            "candidate_name": "",
            "overview": "Overview",
            "recruiter_observations": ["Obs"],
            "open_action_items": [],
            "recommended_next_action": "Advance",
        }
        result = evaluator.evaluate(output, {"workflow_name": "candidate_summary"})
        assert not result.passed

    def test_unknown_workflow_returns_pass(self) -> None:
        evaluator = CompletenessEvaluator()
        result = evaluator.evaluate({"foo": "bar"}, {"workflow_name": "unknown"})
        assert result.passed is True
        assert result.score == 1.0


class TestHallucinationEvaluator:
    def test_claims_supported_by_input(self) -> None:
        evaluator = HallucinationEvaluator()
        output = {"candidate_summary": "Alice Smith has Python and AWS skills"}
        input_data = {"candidate_raw": [{"text": '{"name":"Alice Smith","skills":["Python","AWS"]}'}]}
        result = evaluator.evaluate(output, input_data)
        assert result.passed is True
        assert result.score > 0.5

    def test_unsupported_claims_flagged(self) -> None:
        evaluator = HallucinationEvaluator()
        output = {"summary": "Bob knows Kubernetes and Rust and Go and Java and Kafka and Spark and Hadoop and Cassandra and Redis and Elasticsearch and MongoDB and RabbitMQ"}
        input_data = {"candidate_raw": [{"text": '{"name":"Alice","skills":["Python"]}'}]}
        result = evaluator.evaluate(output, input_data)
        assert not result.passed
        assert result.score < 0.7

    def test_no_input_skips_check(self) -> None:
        evaluator = HallucinationEvaluator()
        result = evaluator.evaluate({"text": "some output"}, None)
        assert result.passed is True
        assert result.score == 1.0

    def test_empty_output_passes(self) -> None:
        evaluator = HallucinationEvaluator()
        result = evaluator.evaluate({}, {"key": "value"})
        assert result.passed is True


class TestConsistencyEvaluator:
    def test_valid_recommendation(self) -> None:
        evaluator = ConsistencyEvaluator()
        output = {
            "candidate_name": "Alice",
            "recommended_next_step": "Move to Final Interview",
            "validated_strengths": ["Python"],
            "identified_concerns": [],
        }
        result = evaluator.evaluate(output, {"workflow_name": "interview_debrief"})
        assert result.passed is True

    def test_invalid_recommendation(self) -> None:
        evaluator = ConsistencyEvaluator()
        output = {
            "recommended_next_step": "INVALID_OPTION",
        }
        result = evaluator.evaluate(output, {"workflow_name": "interview_debrief"})
        assert not result.passed

    def test_invalid_confidence(self) -> None:
        evaluator = ConsistencyEvaluator()
        output = {
            "recruiter_recommendation": "Advance",
            "confidence_level": "INVALID",
        }
        result = evaluator.evaluate(output, {"workflow_name": "hiring_recommendation"})
        assert not result.passed

    def test_evidence_mismatch_flagged(self) -> None:
        evaluator = ConsistencyEvaluator()
        output = {
            "recommended_next_step": "Do Not Advance",
            "validated_strengths": ["Strong Python", "Great comms"],
            "identified_concerns": [],
        }
        result = evaluator.evaluate(output, {"workflow_name": "interview_debrief"})
        assert "risk_factors" in str(result.issues) or "evidence" in str(result.issues) or not result.passed

    def test_unknown_workflow_skips_check(self) -> None:
        evaluator = ConsistencyEvaluator()
        output = {"some_key": "value"}
        result = evaluator.evaluate(output, {"workflow_name": "unknown"})
        assert result.passed is True


class TestPromptRegressionEvaluator:
    def test_no_fixtures_skips(self) -> None:
        evaluator = PromptRegressionEvaluator(fixture_path="/tmp/nonexistent_fixtures")
        result = evaluator.evaluate({"foo": "bar"}, {"workflow_name": "unknown"})
        assert result.passed is True
        assert len(result.issues) == 1
        assert "No regression fixtures" in result.issues[0].message

    def test_matches_existing_fixtures(self, tmp_path: Path) -> None:
        fixture = {
            "workflow_name": "test_wf",
            "output_data": {
                "name": "Alice",
                "score": 92.0,
                "tags": ["a", "b", "c"],
                "notes": "Candidate has strong python skills and excellent communication with the team",
            },
        }
        fixture_file = tmp_path / "test_wf.json"
        fixture_file.write_text(json.dumps(fixture))

        evaluator = PromptRegressionEvaluator(fixture_path=str(tmp_path))
        output = {
            "name": "Alice",
            "score": 92.0,
            "tags": ["a", "b"],
            "notes": "Candidate has strong python skills and communicates well with the team",
        }
        result = evaluator.evaluate(output, {"workflow_name": "test_wf"})
        assert result.passed is True
        assert result.score >= 0.8


class TestEvaluationRunner:
    def test_run_all_workflows(self) -> None:
        with patch.object(EvaluationRunner, "_load_fixture_output") as mock_load:
            mock_load.return_value = {
                "candidate_name": "Alice",
                "overview": "Great",
                "recruiter_observations": ["Obs"],
                "open_action_items": ["Item"],
                "recommended_next_action": "Advance",
                "candidate_id": "cand-1",
                "job_id": "job-1",
                "interview_summary": "Good",
                "validated_strengths": ["S1"],
                "identified_concerns": [],
                "further_evaluation_areas": [],
                "overall_assessment": "Positive",
                "recommended_next_step": "Move to Final Interview",
                "candidate_summary": "Summary",
                "supporting_evidence": ["E1"],
                "caution_evidence": [],
                "risk_factors": [],
                "missing_information": [],
                "confidence_level": "High",
                "executive_summary": "Executive summary",
                "key_strengths": ["K1"],
                "key_risks": [],
                "candidate_overview": {},
                "hiring_recommendation": {},
                "job_title": "Engineer",
                "top_candidates": [],
                "technical_questions": [],
                "behavioral_questions": [],
                "follow_up_questions": [],
                "focus_areas": [],
                "subject": "Hello",
                "email_body": "Body",
                "linkedin_message": "Msg",
                "short_message": "Short",
                "recruiter_recommendation": "Advance",
            }

            runner = EvaluationRunner()
            result = runner.run(EvaluationRunRequest())

        assert len(result.reports) == 7
        assert 0 <= result.summary.average_overall_score <= 1.0
        assert result.summary.total_workflows == 7

    def test_run_single_workflow(self) -> None:
        with patch.object(EvaluationRunner, "_load_fixture_output") as mock_load:
            mock_load.return_value = {
                "candidate_name": "Alice",
                "overview": "Great",
                "recruiter_observations": ["Obs"],
                "open_action_items": ["Item"],
                "recommended_next_action": "Advance",
            }
            runner = EvaluationRunner()
            result = runner.run(EvaluationRunRequest(workflow_name="candidate_summary"))

        assert len(result.reports) == 1
        assert result.reports[0].workflow_name == "candidate_summary"

    def test_report_has_all_evaluators(self) -> None:
        with patch.object(EvaluationRunner, "_load_fixture_output") as mock_load:
            mock_load.return_value = {
                "candidate_name": "Alice",
                "overview": "Great",
                "recruiter_observations": ["Obs"],
                "open_action_items": ["Item"],
                "recommended_next_action": "Advance",
            }
            runner = EvaluationRunner()
            result = runner.run(EvaluationRunRequest(workflow_name="candidate_summary"))

        report = result.reports[0]
        assert report.completeness is not None
        assert report.hallucination is not None
        assert report.consistency is not None
        assert report.prompt_regression is not None
        assert 0 <= report.overall_score <= 1.0


class TestEndpoint:
    async def test_evaluation_run_endpoint(self, client) -> None:
        with patch.object(EvaluationRunner, "_load_fixture_output") as mock_load:
            mock_load.return_value = {
                "candidate_name": "Alice",
                "overview": "Great",
                "recruiter_observations": ["Obs"],
                "open_action_items": ["Item"],
                "recommended_next_action": "Advance",
                "candidate_id": "cand-1",
                "job_id": "job-1",
                "interview_summary": "Good",
                "validated_strengths": ["S1"],
                "identified_concerns": [],
                "further_evaluation_areas": [],
                "overall_assessment": "Positive",
                "recommended_next_step": "Move to Final Interview",
                "candidate_summary": "Summary",
                "supporting_evidence": ["E1"],
                "caution_evidence": [],
                "risk_factors": [],
                "missing_information": [],
                "confidence_level": "High",
                "executive_summary": "Exec",
                "key_strengths": ["K1"],
                "key_risks": [],
                "candidate_overview": {},
                "hiring_recommendation": {},
                "job_title": "Eng",
                "top_candidates": [],
                "technical_questions": [],
                "behavioral_questions": [],
                "follow_up_questions": [],
                "focus_areas": [],
                "subject": "H",
                "email_body": "B",
                "linkedin_message": "M",
                "short_message": "S",
                "recruiter_recommendation": "Advance",
            }

            response = await client.post(
                "/api/v1/evaluation/run",
                json={},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["reports"]) == 7
        assert "summary" in data
        assert data["summary"]["total_workflows"] == 7

    async def test_evaluation_run_single_workflow(self, client) -> None:
        with patch.object(EvaluationRunner, "_load_fixture_output") as mock_load:
            mock_load.return_value = {
                "candidate_name": "Alice",
                "overview": "Great",
                "recruiter_observations": ["Obs"],
                "open_action_items": ["Item"],
                "recommended_next_action": "Advance",
            }
            response = await client.post(
                "/api/v1/evaluation/run",
                json={"workflow_name": "candidate_summary"},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["reports"]) == 1
        assert data["reports"][0]["workflow_name"] == "candidate_summary"
