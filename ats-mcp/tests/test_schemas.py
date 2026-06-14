from datetime import datetime

from pydantic import ValidationError
import pytest

from app.schemas.candidates import (
    Candidate,
    CandidateStage,
    CandidateSource,
    GetCandidateRequest,
    ListCandidatesRequest,
    ListCandidatesResponse,
    RecommendationValue,
)
from app.schemas.comments import Comment, GetCommentsRequest, ListCommentsResponse
from app.schemas.common import ErrorDetail, ErrorResponse, PaginationMeta
from app.schemas.jobs import GetJobRequest, Job, JobRequirement, ListJobsRequest, ListJobsResponse
from app.schemas.tasks import CandidateTask, CandidateTaskStatus, GetTasksRequest, ListTasksResponse
from app.schemas.tools import ListToolsResponse, ToolCallContent, ToolCallRequest, ToolCallResponse, ToolDefinition


class TestCandidateSchemas:
    def test_candidate_full(self) -> None:
        c = Candidate(
            id="cand-1",
            name="Alice Engineer",
            email="alice@example.com",
            skills=["Python", "FastAPI"],
            stage=CandidateStage.INTERVIEW,
            source=CandidateSource.LINKEDIN,
            overall_score=92.5,
            job_fit_score=88.0,
            is_top_candidate=True,
        )
        assert c.name == "Alice Engineer"
        assert c.stage == CandidateStage.INTERVIEW
        assert c.overall_score == 92.5
        assert c.is_top_candidate is True

    def test_candidate_minimal(self) -> None:
        c = Candidate(id="cand-1")
        assert c.name is None
        assert c.skills == []

    def test_get_candidate_request(self) -> None:
        req = GetCandidateRequest(candidate_id="cand-1")
        assert req.candidate_id == "cand-1"

    def test_list_candidates_request_defaults(self) -> None:
        req = ListCandidatesRequest()
        assert req.limit == 50
        assert req.search is None
        assert req.stage is None

    def test_list_candidates_request_invalid_limit(self) -> None:
        with pytest.raises(ValidationError):
            ListCandidatesRequest(limit=0)

    def test_list_candidates_response(self) -> None:
        resp = ListCandidatesResponse(
            candidates=[Candidate(id="c-1", name="A")],
            total=1,
            limit=50,
        )
        assert len(resp.candidates) == 1
        assert resp.total == 1


class TestJobSchemas:
    def test_job_full(self) -> None:
        req = JobRequirement(label="Python", field_type="skill", required=True, order=1)
        j = Job(
            id="job-1",
            title="Engineer",
            company_id="comp-1",
            description="Build things",
            automation_status=True,
            requirements=[req],
            candidate_count=12,
        )
        assert j.title == "Engineer"
        assert len(j.requirements) == 1
        assert j.requirements[0].label == "Python"
        assert j.candidate_count == 12

    def test_job_minimal(self) -> None:
        j = Job(id="j-1", title="T", company_id="c-1")
        assert j.requirements == []
        assert j.candidate_count == 0

    def test_get_job_request(self) -> None:
        req = GetJobRequest(job_id="job-1")
        assert req.job_id == "job-1"

    def test_list_jobs_request(self) -> None:
        req = ListJobsRequest()
        assert req is not None

    def test_list_jobs_response(self) -> None:
        resp = ListJobsResponse(
            jobs=[Job(id="j-1", title="T", company_id="c-1")],
            total=1,
        )
        assert len(resp.jobs) == 1


class TestCommentSchemas:
    def test_comment(self) -> None:
        c = Comment(id="c-1", content="Great fit", author_id="u-1", candidate_id="cand-1")
        assert c.content == "Great fit"
        assert c.created_at is None

    def test_get_comments_request(self) -> None:
        req = GetCommentsRequest(candidate_id="cand-1")
        assert req.candidate_id == "cand-1"

    def test_list_comments_response(self) -> None:
        comments = [Comment(id="c-1", content="A", author_id="u-1", candidate_id="cand-1")]
        resp = ListCommentsResponse(comments=comments, total=len(comments))
        assert resp.total == 1


class TestTaskSchemas:
    def test_candidate_task_full(self) -> None:
        t = CandidateTask(
            id="t-1",
            candidate_id="cand-1",
            recruiter_id="u-1",
            title="Review",
            status=CandidateTaskStatus.IN_PROGRESS,
        )
        assert t.title == "Review"
        assert t.status == CandidateTaskStatus.IN_PROGRESS

    def test_candidate_task_defaults(self) -> None:
        t = CandidateTask(id="t-1", candidate_id="c-1", recruiter_id="u-1", title="T")
        assert t.status == CandidateTaskStatus.TODO

    def test_get_tasks_request(self) -> None:
        req = GetTasksRequest(candidate_id="cand-1")
        assert req.candidate_id == "cand-1"

    def test_list_tasks_response(self) -> None:
        tasks = [CandidateTask(id="t-1", candidate_id="c-1", recruiter_id="u-1", title="T")]
        resp = ListTasksResponse(tasks=tasks, total=len(tasks))
        assert resp.total == 1


class TestToolSchemas:
    def test_tool_definition(self) -> None:
        td = ToolDefinition(
            name="ats_get_candidate",
            description="Get a candidate",
            input_schema={"type": "object", "properties": {}},
        )
        assert td.name == "ats_get_candidate"

    def test_list_tools_response(self) -> None:
        resp = ListToolsResponse(
            tools=[ToolDefinition(name="t1", description="d1")]
        )
        assert len(resp.tools) == 1

    def test_tool_call_request(self) -> None:
        req = ToolCallRequest(name="ats_get_candidate", arguments={"candidate_id": "123"})
        assert req.name == "ats_get_candidate"
        assert req.arguments == {"candidate_id": "123"}

    def test_tool_call_response_success(self) -> None:
        resp = ToolCallResponse(
            content=[ToolCallContent(text='{"id": "123"}')],
            is_error=False,
        )
        assert resp.is_error is False

    def test_tool_call_response_error(self) -> None:
        resp = ToolCallResponse(
            content=[ToolCallContent(text="Not found")],
            is_error=True,
        )
        assert resp.is_error is True


class TestCommonSchemas:
    def test_pagination_meta(self) -> None:
        pm = PaginationMeta(page=1, limit=20, total=100, total_pages=5)
        assert pm.total_pages == 5

    def test_error_detail(self) -> None:
        ed = ErrorDetail(code="NOT_FOUND", message="Not found")
        assert ed.details is None

    def test_error_response(self) -> None:
        er = ErrorResponse(
            error=ErrorDetail(code="ERR", message="Something went wrong", details="More info")
        )
        assert er.error.code == "ERR"
