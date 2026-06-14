from datetime import datetime

from pydantic import ValidationError
import pytest

from app.schemas.analytics import (
    DashboardResponse,
    FunnelResponse,
    FunnelStage,
    HiringSpeedResponse,
    PipelineHealthResponse,
    PipelineHealthStage,
    SourceAnalyticsResponse,
    SourceMetric,
)
from app.schemas.interviews import (
    InterviewEvent,
    InterviewEventKind,
    InterviewEventStatus,
    ListInterviewsRequest,
    ListInterviewsResponse,
)
from app.schemas.matching import (
    MatchCandidatesRequest,
    MatchCandidatesResponse,
    MatchResult,
)
from app.schemas.outreach import (
    EmailActivity,
    ListEmailHistoryRequest,
    ListEmailHistoryResponse,
    SendEmailRequest,
    SendEmailResponse,
)
from app.schemas.resume import (
    GetProcessingStatusRequest,
    ProcessingJob,
    ProcessingStatus,
    ProcessingStatusResponse,
    ResumeSearchRequest,
    ResumeSearchResponse,
)


class TestInterviewSchemas:
    def test_interview_event_minimal(self) -> None:
        event = InterviewEvent(id="int-1", recruiter_id="u-1")
        assert event.title == ""
        assert event.status == InterviewEventStatus.PENDING
        assert event.kind == InterviewEventKind.INTERVIEW

    def test_interview_event_full(self) -> None:
        event = InterviewEvent(
            id="int-1",
            candidate_id="cand-1",
            job_id="job-1",
            recruiter_id="u-1",
            title="Technical Screen",
            status=InterviewEventStatus.CONFIRMED,
            start_time=datetime(2026, 6, 15, 14, 0, 0),
            end_time=datetime(2026, 6, 15, 15, 0, 0),
        )
        assert event.title == "Technical Screen"
        assert event.status == InterviewEventStatus.CONFIRMED

    def test_list_interviews_request_defaults(self) -> None:
        req = ListInterviewsRequest()
        assert req.limit == 50
        assert req.candidate_id is None

    def test_list_interviews_request_invalid_limit(self) -> None:
        with pytest.raises(ValidationError):
            ListInterviewsRequest(limit=0)

    def test_list_interviews_response(self) -> None:
        resp = ListInterviewsResponse(interviews=[InterviewEvent(id="i-1", recruiter_id="u-1")])
        assert resp.total == 0  # not auto-computed
        resp2 = ListInterviewsResponse(
            interviews=[InterviewEvent(id="i-1", recruiter_id="u-1")],
            total=1,
        )
        assert resp2.total == 1


class TestOutreachSchemas:
    def test_email_activity(self) -> None:
        email = EmailActivity(
            id="e-1",
            candidate_id="c-1",
            recruiter_id="r-1",
            subject="Interview Invitation",
            body="Dear candidate...",
        )
        assert email.subject == "Interview Invitation"

    def test_list_email_history_request(self) -> None:
        req = ListEmailHistoryRequest(candidate_id="c-1")
        assert req.candidate_id == "c-1"

    def test_list_email_history_response(self) -> None:
        resp = ListEmailHistoryResponse(emails=[EmailActivity(id="e-1", candidate_id="c-1", recruiter_id="r-1", subject="S", body="B")])
        assert resp.total == 0

    def test_send_email_request(self) -> None:
        req = SendEmailRequest(candidate_id="c-1", subject="Hello", body="Body")
        assert req.subject == "Hello"

    def test_send_email_response(self) -> None:
        resp = SendEmailResponse(email_id="e-1", sent=True)
        assert resp.sent is True


class TestAnalyticsSchemas:
    def test_funnel_stage(self) -> None:
        fs = FunnelStage(stage="APPLIED", count=100, conversion_rate=0.8)
        assert fs.count == 100

    def test_funnel_response(self) -> None:
        resp = FunnelResponse(stages=[FunnelStage(stage="APPLIED", count=50)])
        assert len(resp.stages) == 1

    def test_hiring_speed_response(self) -> None:
        resp = HiringSpeedResponse(avg_time_to_fill_days=15.5, total_hires=5)
        assert resp.avg_time_to_fill_days == 15.5

    def test_source_metric(self) -> None:
        sm = SourceMetric(source="LinkedIn", candidates=30)
        assert sm.candidates == 30

    def test_source_analytics_response(self) -> None:
        resp = SourceAnalyticsResponse(sources=[SourceMetric(source="Referral", candidates=10)])
        assert len(resp.sources) == 1

    def test_pipeline_health_stage(self) -> None:
        phs = PipelineHealthStage(stage="INTERVIEW", candidate_count=15, health="healthy")
        assert phs.health == "healthy"

    def test_pipeline_health_response(self) -> None:
        resp = PipelineHealthResponse(stages=[PipelineHealthStage(stage="APPLIED", candidate_count=100)])
        assert resp.stages[0].candidate_count == 100

    def test_dashboard_response(self) -> None:
        resp = DashboardResponse(total_candidates=200, total_jobs=10, total_hires=5)
        assert resp.total_candidates == 200
        assert resp.total_hires == 5


class TestMatchingSchemas:
    def test_match_result(self) -> None:
        mr = MatchResult(
            candidate_id="c-1",
            candidate_name="Alice",
            job_id="j-1",
            overall_score=92.5,
            strengths=["Python", "Leadership"],
            gaps=["No Kubernetes"],
        )
        assert mr.overall_score == 92.5
        assert len(mr.strengths) == 2

    def test_match_candidates_request(self) -> None:
        req = MatchCandidatesRequest(job_id="j-1", limit=5)
        assert req.job_id == "j-1"
        assert req.limit == 5

    def test_match_candidates_request_invalid_limit(self) -> None:
        with pytest.raises(ValidationError):
            MatchCandidatesRequest(job_id="j-1", limit=0)

    def test_match_candidates_response(self) -> None:
        resp = MatchCandidatesResponse(job_id="j-1", matches=[MatchResult(candidate_id="c-1", job_id="j-1")])
        assert resp.job_id == "j-1"
        assert len(resp.matches) == 1


class TestResumeSchemas:
    def test_processing_job(self) -> None:
        pj = ProcessingJob(id="pj-1", candidate_id="c-1", job_id="j-1", status=ProcessingStatus.PENDING)
        assert pj.status == ProcessingStatus.PENDING
        assert pj.retry_count == 0

    def test_get_processing_status_request(self) -> None:
        req = GetProcessingStatusRequest(candidate_id="c-1")
        assert req.candidate_id == "c-1"

    def test_processing_status_response(self) -> None:
        resp = ProcessingStatusResponse(candidate_id="c-1", status=ProcessingStatus.ANALYZED)
        assert resp.status == ProcessingStatus.ANALYZED

    def test_resume_search_request(self) -> None:
        req = ResumeSearchRequest(query="Python developer", limit=5)
        assert req.query == "Python developer"
        assert req.limit == 5

    def test_resume_search_request_invalid_limit(self) -> None:
        with pytest.raises(ValidationError):
            ResumeSearchRequest(query="test", limit=0)

    def test_resume_search_response(self) -> None:
        resp = ResumeSearchResponse(candidates=[{"id": "c-1"}], total=1)
        assert len(resp.candidates) == 1


class TestErrorTypes:
    from app.core.errors import (
        BackendTimeoutError,
        NotImplementedError_,
        RateLimitError,
        ValidationError as ToolValidationError,
    )

    def test_backend_timeout_error(self) -> None:
        err = self.BackendTimeoutError("Request took too long")
        assert err.code == "BACKEND_TIMEOUT"

    def test_rate_limit_error(self) -> None:
        err = self.RateLimitError(retry_after=5.0)
        assert err.code == "RATE_LIMITED"
        assert "5.0" in err.message

    def test_not_implemented_error(self) -> None:
        err = self.NotImplementedError_("ats_schedule_interview")
        assert err.code == "NOT_IMPLEMENTED"
        assert "ats_schedule_interview" in err.message

    def test_validation_error_tool(self) -> None:
        err = self.ToolValidationError("Invalid field: skills")
        assert err.code == "VALIDATION_ERROR"
        assert err.details == "Invalid field: skills"
