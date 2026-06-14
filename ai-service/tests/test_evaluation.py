import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.evaluation.store import FeedbackStore, get_feedback_store
from app.evaluation.tracing import TracerStore, WorkflowTracer, get_tracer_store
from app.schemas.evaluation import (
    FeedbackRating,
    FeedbackRecord,
    FeedbackStats,
    WorkflowMetrics,
    WorkflowTrace,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    FeedbackStore._store = None
    TracerStore._tracer_store = None
    yield
    FeedbackStore._store = None
    TracerStore._tracer_store = None


@pytest.fixture
def tmp_store_path(tmp_path: Path) -> str:
    return str(tmp_path / "evaluation")


@pytest.fixture
def store(tmp_store_path: str) -> FeedbackStore:
    return FeedbackStore(store_path=tmp_store_path)


@pytest.fixture
def tracer_store(tmp_store_path: str) -> TracerStore:
    return TracerStore(store_path=tmp_store_path)


class TestFeedbackStore:
    def test_add_feedback(self, store: FeedbackStore) -> None:
        record = store.add_feedback(
            workflow_name="candidate-summary",
            candidate_id="cand-1",
            rating=FeedbackRating.UP,
            feedback_text="Great summary",
        )
        assert record.id
        assert record.workflow_name == "candidate-summary"
        assert record.candidate_id == "cand-1"
        assert record.rating == FeedbackRating.UP
        assert record.feedback_text == "Great summary"
        assert record.timestamp is not None

    def test_add_down_feedback(self, store: FeedbackStore) -> None:
        record = store.add_feedback(
            workflow_name="hiring-recommendation",
            candidate_id="cand-2",
            rating=FeedbackRating.DOWN,
            feedback_text="Missed key risks",
        )
        assert record.rating == FeedbackRating.DOWN

    def test_get_all_feedback(self, store: FeedbackStore) -> None:
        store.add_feedback("wf1", "c1", FeedbackRating.UP)
        store.add_feedback("wf2", "c2", FeedbackRating.DOWN)
        store.add_feedback("wf1", "c3", FeedbackRating.UP)

        all_fb = store.get_all_feedback()
        assert len(all_fb) == 3

    def test_get_feedback_by_workflow(self, store: FeedbackStore) -> None:
        store.add_feedback("wf1", "c1", FeedbackRating.UP)
        store.add_feedback("wf2", "c2", FeedbackRating.DOWN)
        store.add_feedback("wf1", "c3", FeedbackRating.UP)

        wf1_fb = store.get_feedback_by_workflow("wf1")
        assert len(wf1_fb) == 2

        wf2_fb = store.get_feedback_by_workflow("wf2")
        assert len(wf2_fb) == 1

        wf3_fb = store.get_feedback_by_workflow("wf3")
        assert len(wf3_fb) == 0

    def test_get_feedback_by_candidate(self, store: FeedbackStore) -> None:
        store.add_feedback("wf1", "c1", FeedbackRating.UP)
        store.add_feedback("wf2", "c1", FeedbackRating.DOWN)
        store.add_feedback("wf1", "c2", FeedbackRating.UP)

        c1_fb = store.get_feedback_by_candidate("c1")
        assert len(c1_fb) == 2

        c2_fb = store.get_feedback_by_candidate("c2")
        assert len(c2_fb) == 1

    def test_empty_stats(self, store: FeedbackStore) -> None:
        stats = store.get_stats()
        assert stats.total_feedback == 0
        assert stats.approval_rate == 0.0
        assert stats.rejection_rate == 0.0
        assert stats.workflow_usage == {}

    def test_stats_with_feedback(self, store: FeedbackStore) -> None:
        store.add_feedback("wf1", "c1", FeedbackRating.UP)
        store.add_feedback("wf1", "c2", FeedbackRating.UP)
        store.add_feedback("wf1", "c3", FeedbackRating.DOWN)
        store.add_feedback("wf2", "c4", FeedbackRating.UP)

        stats = store.get_stats()
        assert stats.total_feedback == 4
        assert stats.approval_rate == 75.0
        assert stats.rejection_rate == 25.0
        assert stats.workflow_usage == {"wf1": 3, "wf2": 1}

    def test_workflow_metrics(self, store: FeedbackStore) -> None:
        store.add_feedback("wf1", "c1", FeedbackRating.UP)
        store.add_feedback("wf1", "c2", FeedbackRating.UP)
        store.add_feedback("wf1", "c3", FeedbackRating.DOWN)

        stats = store.get_stats()
        assert len(stats.workflow_metrics) == 1
        wf1_metrics = stats.workflow_metrics[0]
        assert wf1_metrics.workflow_name == "wf1"
        assert wf1_metrics.total == 3
        assert wf1_metrics.approvals == 2
        assert wf1_metrics.rejections == 1
        assert wf1_metrics.approval_rate == pytest.approx(66.7, 0.1)

    def test_persists_to_disk(self, tmp_store_path: str) -> None:
        store1 = FeedbackStore(store_path=tmp_store_path)
        store1.add_feedback("wf1", "c1", FeedbackRating.UP, "Great")
        store1.add_feedback("wf2", "c2", FeedbackRating.DOWN, "Bad")

        store2 = FeedbackStore(store_path=tmp_store_path)
        all_fb = store2.get_all_feedback()
        assert len(all_fb) == 2
        assert all_fb[0].feedback_text == "Great"
        assert all_fb[1].feedback_text == "Bad"

    def test_supports_prompt_and_model(self, store: FeedbackStore) -> None:
        record = store.add_feedback(
            workflow_name="test",
            candidate_id="c1",
            rating=FeedbackRating.UP,
            feedback_text="ok",
            prompt_template="test_prompt.md",
            model_used="gpt-4",
        )
        assert record.prompt_template == "test_prompt.md"
        assert record.model_used == "gpt-4"


class TestTracerStore:
    def test_start_trace(self, tracer_store: TracerStore) -> None:
        run_id = tracer_store.start_trace(
            workflow_name="hiring-recommendation",
            candidate_id="cand-1",
            prompt_template="hiring_recommendation.md",
            model_used="gpt-4o",
        )
        assert run_id
        trace = tracer_store.get_trace(run_id)
        assert trace is not None
        assert trace.workflow_name == "hiring-recommendation"
        assert trace.candidate_id == "cand-1"
        assert trace.prompt_template == "hiring_recommendation.md"
        assert trace.model_used == "gpt-4o"
        assert trace.started_at is not None
        assert trace.completed_at is None

    def test_complete_trace(self, tracer_store: TracerStore) -> None:
        run_id = tracer_store.start_trace("wf1", "c1")
        tracer_store.complete_trace(run_id, output_snapshot={"result": "pass"})

        trace = tracer_store.get_trace(run_id)
        assert trace is not None
        assert trace.completed_at is not None
        assert trace.output_snapshot == {"result": "pass"}

    def test_get_trace_not_found(self, tracer_store: TracerStore) -> None:
        trace = tracer_store.get_trace("nonexistent")
        assert trace is None

    def test_get_traces_by_workflow(self, tracer_store: TracerStore) -> None:
        tracer_store.start_trace("wf1", "c1")
        tracer_store.start_trace("wf2", "c2")
        tracer_store.start_trace("wf1", "c3")

        wf1_traces = tracer_store.get_traces_by_workflow("wf1")
        assert len(wf1_traces) == 2

        wf2_traces = tracer_store.get_traces_by_workflow("wf2")
        assert len(wf2_traces) == 1

    def test_get_traces_by_candidate(self, tracer_store: TracerStore) -> None:
        tracer_store.start_trace("wf1", "c1")
        tracer_store.start_trace("wf2", "c1")
        tracer_store.start_trace("wf1", "c2")

        c1_traces = tracer_store.get_traces_by_candidate("c1")
        assert len(c1_traces) == 2

    def test_persists_to_disk(self, tmp_store_path: str) -> None:
        ts1 = TracerStore(store_path=tmp_store_path)
        run_id = ts1.start_trace("wf1", "c1", "prompt.md", "model-x")
        ts1.complete_trace(run_id, {"key": "val"})

        ts2 = TracerStore(store_path=tmp_store_path)
        trace = ts2.get_trace(run_id)
        assert trace is not None
        assert trace.workflow_name == "wf1"
        assert trace.output_snapshot == {"key": "val"}


class TestWorkflowTracer:
    def test_tracer_lifecycle(self, tmp_store_path: str) -> None:
        with patch("app.evaluation.tracing.get_tracer_store") as mock_get:
            real_store = TracerStore(store_path=tmp_store_path)
            mock_get.return_value = real_store

            tracer = WorkflowTracer(workflow_name="test-wf", candidate_id="cand-1")
            tracer.prompt_template = "test.md"
            tracer.model_used = "gpt-4"

            run_id = tracer.start()
            assert run_id
            assert tracer.run_id == run_id

            tracer.complete(output={"result": "ok"})
            trace = real_store.get_trace(run_id)
            assert trace is not None
            assert trace.completed_at is not None
            assert trace.output_snapshot == {"result": "ok"}


class TestSchemas:
    def test_feedback_rating_values(self) -> None:
        assert FeedbackRating.UP.value == "up"
        assert FeedbackRating.DOWN.value == "down"

    def test_feedback_request_defaults(self) -> None:
        from app.schemas.evaluation import FeedbackRequest

        req = FeedbackRequest(workflow_name="wf", candidate_id="c1", rating=FeedbackRating.UP)
        assert req.feedback_text == ""

    def test_workflow_metrics_defaults(self) -> None:
        metrics = WorkflowMetrics(workflow_name="wf1")
        assert metrics.total == 0
        assert metrics.approvals == 0
        assert metrics.rejections == 0
        assert metrics.approval_rate == 0.0

    def test_feedback_stats_empty(self) -> None:
        stats = FeedbackStats()
        assert stats.total_feedback == 0
        assert stats.approval_rate == 0.0
        assert stats.workflow_usage == {}

    def test_workflow_trace_defaults(self) -> None:
        trace = WorkflowTrace(
            run_id="r1", workflow_name="wf1", candidate_id="c1",
            prompt_template="p.md", model_used="m",
        )
        assert trace.started_at is not None
        assert trace.completed_at is None
        assert trace.output_snapshot == {}

    def test_feedback_record_full(self) -> None:
        from datetime import datetime
        record = FeedbackRecord(
            id="fb-1", workflow_name="wf", candidate_id="c1",
            rating=FeedbackRating.DOWN, feedback_text="Bad",
            timestamp=datetime.now(), prompt_template="p.md",
            model_used="gpt-4",
        )
        assert record.prompt_template == "p.md"
        assert record.model_used == "gpt-4"


class TestEndpoints:
    @patch("app.api.v1.evaluation.get_feedback_store")
    async def test_submit_feedback(self, mock_get_store: MagicMock, client) -> None:
        mock_store = MagicMock()
        mock_store.add_feedback.return_value = FeedbackRecord(
            id="fb-1", workflow_name="candidate-summary",
            candidate_id="cand-1", rating=FeedbackRating.UP,
            feedback_text="Great work", timestamp="2026-01-01T00:00:00",
            prompt_template="", model_used="",
        )
        mock_get_store.return_value = mock_store

        response = await client.post(
            "/api/v1/feedback",
            json={
                "workflow_name": "candidate-summary",
                "candidate_id": "cand-1",
                "rating": "up",
                "feedback_text": "Great work",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "fb-1"
        assert data["rating"] == "up"

    @patch("app.api.v1.evaluation.get_feedback_store")
    async def test_list_feedback(self, mock_get_store: MagicMock, client) -> None:
        mock_store = MagicMock()
        mock_store.get_all_feedback.return_value = [
            FeedbackRecord(id="f1", workflow_name="wf1", candidate_id="c1",
                           rating=FeedbackRating.UP, feedback_text="",
                           timestamp="2026-01-01T00:00:00",
                           prompt_template="", model_used=""),
        ]
        mock_get_store.return_value = mock_store

        response = await client.get("/api/v1/feedback")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    @patch("app.api.v1.evaluation.get_feedback_store")
    async def test_feedback_stats(self, mock_get_store: MagicMock, client) -> None:
        mock_store = MagicMock()
        mock_store.get_stats.return_value = FeedbackStats(
            total_feedback=10, approval_rate=80.0, rejection_rate=20.0,
            workflow_usage={"wf1": 10},
            workflow_metrics=[
                WorkflowMetrics(workflow_name="wf1", total=10, approvals=8,
                                rejections=2, approval_rate=80.0),
            ],
        )
        mock_get_store.return_value = mock_store

        response = await client.get("/api/v1/feedback/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_feedback"] == 10
        assert data["approval_rate"] == 80.0

    async def test_submit_feedback_invalid_rating(self, client) -> None:
        response = await client.post(
            "/api/v1/feedback",
            json={
                "workflow_name": "wf",
                "candidate_id": "c1",
                "rating": "invalid",
            },
        )
        assert response.status_code == 422

    async def test_submit_feedback_missing_required(self, client) -> None:
        response = await client.post(
            "/api/v1/feedback",
            json={"rating": "up"},
        )
        assert response.status_code == 422

    @patch("app.api.v1.evaluation.get_feedback_store")
    async def test_feedback_health(self, mock_get_store: MagicMock, client) -> None:
        mock_store = MagicMock()
        mock_store.get_all_feedback.return_value = [1, 2, 3]
        mock_get_store.return_value = mock_store

        response = await client.get("/api/v1/feedback/health")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Evaluation system operational"
