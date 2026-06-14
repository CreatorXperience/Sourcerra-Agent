from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.prompts.dashboard import get_prompt_dashboard
from app.prompts.experiments import ExperimentManager
from app.prompts.registry import PromptRegistry
from app.schemas.evaluation import FeedbackRating, FeedbackRecord, WorkflowTrace
from app.schemas.prompts import (
    ExperimentConfig,
    PromptDashboard,
    PromptStatus,
    PromptVersion,
    PromptVersionMetrics,
    RolloutStrategy,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    PromptRegistry._registry = None
    ExperimentManager._manager = None
    yield
    PromptRegistry._registry = None
    ExperimentManager._manager = None


@pytest.fixture
def tmp_store_path(tmp_path: Path) -> str:
    return str(tmp_path / "evaluation")


@pytest.fixture
def registry(tmp_store_path: str) -> PromptRegistry:
    return PromptRegistry(store_path=tmp_store_path)


@pytest.fixture
def experiment_manager(tmp_store_path: str) -> ExperimentManager:
    return ExperimentManager(store_path=tmp_store_path)


class TestPromptSchemas:
    def test_prompt_version_defaults(self) -> None:
        v = PromptVersion(prompt_id="p1", workflow_name="candidate_summary", version=1)
        assert v.status == PromptStatus.DRAFT
        assert v.content == ""

    def test_prompt_status_values(self) -> None:
        assert PromptStatus.DRAFT.value == "draft"
        assert PromptStatus.ACTIVE.value == "active"
        assert PromptStatus.ARCHIVED.value == "archived"

    def test_rollout_strategy_values(self) -> None:
        assert RolloutStrategy.FULL_A.value == "full_a"
        assert RolloutStrategy.SPLIT_50.value == "split_50"
        assert RolloutStrategy.WEIGHTED.value == "weighted"

    def test_experiment_config_defaults(self) -> None:
        e = ExperimentConfig(
            experiment_id="e1", workflow_name="wf1",
            prompt_id_a="p1", prompt_id_b="p2",
        )
        assert e.strategy == RolloutStrategy.FULL_A
        assert e.weight_a == 1.0
        assert e.enabled is True

    def test_prompt_version_metrics_defaults(self) -> None:
        m = PromptVersionMetrics(prompt_id="p1", workflow_name="wf1", version=1)
        assert m.usage_count == 0
        assert m.approval_rate == 0.0

    def test_dashboard_best_version(self) -> None:
        v1 = PromptVersionMetrics(prompt_id="p1", workflow_name="wf1", version=1,
                                  usage_count=10, approval_rate=80.0, average_evaluation_score=90.0)
        v2 = PromptVersionMetrics(prompt_id="p2", workflow_name="wf1", version=2,
                                  usage_count=5, approval_rate=60.0, average_evaluation_score=70.0)
        dashboard = PromptDashboard(workflow_name="wf1", versions=[v1, v2])
        best = dashboard.best_version()
        assert best is not None
        assert best.prompt_id == "p1"

    def test_dashboard_best_version_no_data(self) -> None:
        v1 = PromptVersionMetrics(prompt_id="p1", workflow_name="wf1", version=1)
        dashboard = PromptDashboard(workflow_name="wf1", versions=[v1])
        assert dashboard.best_version() is None


class TestPromptRegistry:
    def test_register_prompt(self, registry: PromptRegistry) -> None:
        v = registry.register("candidate_summary", "You are a helpful assistant")
        assert v.workflow_name == "candidate_summary"
        assert v.version == 1
        assert v.status == PromptStatus.DRAFT
        assert v.content == "You are a helpful assistant"
        assert v.prompt_id

    def test_register_increments_version(self, registry: PromptRegistry) -> None:
        v1 = registry.register("wf1", "prompt v1")
        assert v1.version == 1

        v2 = registry.register("wf1", "prompt v2")
        assert v2.version == 2

        v3 = registry.register("wf1", "prompt v3")
        assert v3.version == 3

    def test_activate_prompt(self, registry: PromptRegistry) -> None:
        v = registry.register("wf1", "content")
        assert v.status == PromptStatus.DRAFT

        activated = registry.activate(v.prompt_id)
        assert activated is not None
        assert activated.status == PromptStatus.ACTIVE

        stored = registry.get_active("wf1")
        assert stored is not None
        assert stored.prompt_id == v.prompt_id

    def test_activate_archives_previous_active(self, registry: PromptRegistry) -> None:
        v1 = registry.register("wf1", "v1")
        registry.activate(v1.prompt_id)
        assert registry.get_active("wf1").prompt_id == v1.prompt_id

        v2 = registry.register("wf1", "v2")
        registry.activate(v2.prompt_id)

        assert registry.get_version(v1.prompt_id).status == PromptStatus.ARCHIVED
        assert registry.get_active("wf1").prompt_id == v2.prompt_id

    def test_archive_prompt(self, registry: PromptRegistry) -> None:
        v = registry.register("wf1", "content")
        registry.activate(v.prompt_id)
        assert registry.archive(v.prompt_id) is not None
        assert registry.get_version(v.prompt_id).status == PromptStatus.ARCHIVED

    def test_get_active_none_when_no_active(self, registry: PromptRegistry) -> None:
        registry.register("wf1", "content")
        assert registry.get_active("wf1") is None

    def test_get_version_by_number(self, registry: PromptRegistry) -> None:
        registry.register("wf1", "v1")
        v2 = registry.register("wf1", "v2")
        registry.register("wf1", "v3")

        found = registry.get_version_by_number("wf1", 2)
        assert found is not None
        assert found.prompt_id == v2.prompt_id

        missing = registry.get_version_by_number("wf1", 99)
        assert missing is None

    def test_list_versions_all(self, registry: PromptRegistry) -> None:
        registry.register("wf1", "v1")
        registry.register("wf1", "v2")
        registry.register("wf2", "v1")

        all_v = registry.list_versions()
        assert len(all_v) == 3

    def test_list_versions_by_workflow(self, registry: PromptRegistry) -> None:
        registry.register("wf1", "v1")
        registry.register("wf1", "v2")
        registry.register("wf2", "v1")

        wf1_v = registry.list_versions("wf1")
        assert len(wf1_v) == 2

    def test_persists_to_disk(self, tmp_store_path: str) -> None:
        r1 = PromptRegistry(store_path=tmp_store_path)
        v = r1.register("wf1", "content")
        r1.activate(v.prompt_id)

        r2 = PromptRegistry(store_path=tmp_store_path)
        versions = r2.list_versions("wf1")
        assert len(versions) == 1
        assert versions[0].status == PromptStatus.ACTIVE

    def test_activate_returns_none_for_missing(self, registry: PromptRegistry) -> None:
        assert registry.activate("nonexistent") is None

    def test_archive_returns_none_for_missing(self, registry: PromptRegistry) -> None:
        assert registry.archive("nonexistent") is None


class TestExperimentManager:
    def test_create_experiment(self, experiment_manager: ExperimentManager) -> None:
        e = experiment_manager.create_experiment(
            workflow_name="candidate_summary",
            prompt_id_a="p1",
            prompt_id_b="p2",
            strategy=RolloutStrategy.SPLIT_50,
        )
        assert e.experiment_id
        assert e.workflow_name == "candidate_summary"
        assert e.prompt_id_a == "p1"
        assert e.prompt_id_b == "p2"
        assert e.strategy == RolloutStrategy.SPLIT_50
        assert e.enabled is True

    def test_get_active_experiment(self, experiment_manager: ExperimentManager) -> None:
        e = experiment_manager.create_experiment("wf1", "p1", "p2")
        active = experiment_manager.get_active_experiment("wf1")
        assert active is not None
        assert active.experiment_id == e.experiment_id

    def test_get_active_experiment_returns_none_when_disabled(
        self, experiment_manager: ExperimentManager,
    ) -> None:
        e = experiment_manager.create_experiment("wf1", "p1", "p2")
        experiment_manager.disable_experiment(e.experiment_id)
        assert experiment_manager.get_active_experiment("wf1") is None

    def test_list_experiments(self, experiment_manager: ExperimentManager) -> None:
        experiment_manager.create_experiment("wf1", "p1", "p2")
        experiment_manager.create_experiment("wf2", "p3", "p4")
        experiment_manager.create_experiment("wf1", "p5", "p6")

        all_e = experiment_manager.list_experiments()
        assert len(all_e) == 3

        wf1_e = experiment_manager.list_experiments("wf1")
        assert len(wf1_e) == 2

    def test_disable_experiment(self, experiment_manager: ExperimentManager) -> None:
        e = experiment_manager.create_experiment("wf1", "p1", "p2")
        assert experiment_manager.disable_experiment(e.experiment_id) is True
        assert experiment_manager.disable_experiment("nonexistent") is False
        assert experiment_manager.get_experiment(e.experiment_id).enabled is False

    def test_assign_without_experiment_falls_back_to_registry(
        self, experiment_manager: ExperimentManager, tmp_store_path: str,
    ) -> None:
        registry = PromptRegistry(store_path=tmp_store_path)
        v = registry.register("wf1", "content")
        registry.activate(v.prompt_id)

        with patch("app.prompts.registry.get_prompt_registry", return_value=registry):
            prompt_id, version_str, experiment_id = experiment_manager.assign("wf1", "cand-1")
            assert prompt_id == v.prompt_id
            assert version_str == "1"
            assert experiment_id == "default"

    def test_assign_without_experiment_and_no_active_returns_empty(
        self, experiment_manager: ExperimentManager,
    ) -> None:
        PromptRegistry._registry = PromptRegistry()

        prompt_id, version_str, experiment_id = experiment_manager.assign("wf1", "cand-1")
        assert prompt_id == ""
        assert version_str == "0"

    def test_assign_full_a(self, experiment_manager: ExperimentManager) -> None:
        experiment_manager.create_experiment("wf1", "p1", "p2", strategy=RolloutStrategy.FULL_A)
        result = [experiment_manager.assign("wf1", "c1") for _ in range(10)]
        for prompt_id, _, _ in result:
            assert prompt_id == "p1"

    def test_assign_split_50(self, experiment_manager: ExperimentManager) -> None:
        experiment_manager.create_experiment("wf1", "p1", "p2", strategy=RolloutStrategy.SPLIT_50)
        results = [experiment_manager.assign("wf1", f"c{i}") for i in range(100)]
        a_count = sum(1 for p, _, _ in results if p == "p1")
        b_count = sum(1 for p, _, _ in results if p == "p2")
        assert 30 <= a_count <= 70
        assert 30 <= b_count <= 70

    def test_assign_weighted(self, experiment_manager: ExperimentManager) -> None:
        experiment_manager.create_experiment(
            "wf1", "p1", "p2", strategy=RolloutStrategy.WEIGHTED, weight_a=0.8,
        )
        results = [experiment_manager.assign("wf1", f"c{i}") for i in range(100)]
        a_count = sum(1 for p, _, _ in results if p == "p1")
        assert 60 <= a_count <= 100

    def test_persists_to_disk(self, tmp_store_path: str) -> None:
        m1 = ExperimentManager(store_path=tmp_store_path)
        m1.create_experiment("wf1", "p1", "p2")

        m2 = ExperimentManager(store_path=tmp_store_path)
        experiments = m2.list_experiments()
        assert len(experiments) == 1


class TestBedrockIntegration:
    def test_tracer_captures_prompt_id_and_version(self, tmp_store_path: str) -> None:
        from app.evaluation.tracing import TracerStore, WorkflowTracer

        store = TracerStore(store_path=tmp_store_path)

        with patch("app.evaluation.tracing.get_tracer_store", return_value=store):
            tracer = WorkflowTracer(workflow_name="candidate_summary", candidate_id="cand-1")
            tracer.prompt_template = "test_prompt.md"
            tracer.model_used = "gpt-4"
            tracer.prompt_id = "p123"
            tracer.prompt_version = 3

            run_id = tracer.start()
            tracer.complete(output={"result": "ok"})

            trace = store.get_trace(run_id)
            assert trace is not None
            assert trace.prompt_id == "p123"
            assert trace.prompt_version == 3
            assert trace.workflow_name == "candidate_summary"

    def test_dashboard_aggregates_metrics_by_prompt_version(
        self, tmp_store_path: str,
    ) -> None:
        registry = PromptRegistry(store_path=tmp_store_path)
        v1 = registry.register("candidate_summary", "v1 content")
        registry.activate(v1.prompt_id)
        v2 = registry.register("candidate_summary", "v2 content")

        from app.evaluation.store import FeedbackStore

        store = FeedbackStore(store_path=tmp_store_path)
        store.add_feedback(
            workflow_name="candidate_summary", candidate_id="c1",
            rating=FeedbackRating.UP, prompt_template=v1.prompt_id,
        )
        store.add_feedback(
            workflow_name="candidate_summary", candidate_id="c2",
            rating=FeedbackRating.DOWN, prompt_template=v1.prompt_id,
        )

        with (
            patch("app.prompts.dashboard.get_prompt_registry", return_value=registry),
            patch("app.prompts.dashboard.get_feedback_store", return_value=store),
        ):
            dashboard = get_prompt_dashboard("candidate_summary")
            assert dashboard.workflow_name == "candidate_summary"
            assert len(dashboard.versions) == 2
            assert dashboard.active_version is not None
            assert dashboard.active_version.prompt_id == v1.prompt_id

            v1_metrics = [m for m in dashboard.versions if m.prompt_id == v1.prompt_id][0]
            assert v1_metrics.approval_rate == 50.0
            assert v1_metrics.rejection_rate == 50.0


class TestEndpoint:
    @patch("app.api.v1.prompts.get_prompt_registry")
    async def test_list_versions(self, mock_get: MagicMock, client) -> None:
        mock_reg = MagicMock()
        mock_reg.list_versions.return_value = [
            PromptVersion(prompt_id="p1", workflow_name="wf1", version=1),
        ]
        mock_get.return_value = mock_reg

        response = await client.get("/api/v1/prompts/versions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["prompt_id"] == "p1"

    @patch("app.api.v1.prompts.get_prompt_registry")
    async def test_register_prompt(self, mock_get: MagicMock, client) -> None:
        mock_reg = MagicMock()
        mock_reg.register.return_value = PromptVersion(
            prompt_id="p1", workflow_name="wf1", version=1,
        )
        mock_get.return_value = mock_reg

        response = await client.post(
            "/api/v1/prompts/versions",
            json={"workflow_name": "wf1", "content": "test prompt"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["prompt_id"] == "p1"
        assert data["version"] == 1

    @patch("app.api.v1.prompts.get_prompt_registry")
    async def test_activate_version(self, mock_get: MagicMock, client) -> None:
        mock_reg = MagicMock()
        mock_reg.activate.return_value = PromptVersion(
            prompt_id="p1", workflow_name="wf1", version=1, status=PromptStatus.ACTIVE,
        )
        mock_get.return_value = mock_reg

        response = await client.post("/api/v1/prompts/versions/p1/activate")
        assert response.status_code == 200
        assert response.json()["status"] == "active"

    @patch("app.api.v1.prompts.get_prompt_registry")
    async def test_activate_version_not_found(self, mock_get: MagicMock, client) -> None:
        mock_reg = MagicMock()
        mock_reg.activate.return_value = None
        mock_get.return_value = mock_reg

        response = await client.post("/api/v1/prompts/versions/p1/activate")
        assert response.status_code == 404

    @patch("app.api.v1.prompts.get_prompt_registry")
    async def test_archive_version(self, mock_get: MagicMock, client) -> None:
        mock_reg = MagicMock()
        mock_reg.archive.return_value = PromptVersion(
            prompt_id="p1", workflow_name="wf1", version=1, status=PromptStatus.ARCHIVED,
        )
        mock_get.return_value = mock_reg

        response = await client.post("/api/v1/prompts/versions/p1/archive")
        assert response.status_code == 200
        assert response.json()["status"] == "archived"

    @patch("app.api.v1.prompts.get_experiment_manager")
    async def test_list_experiments(self, mock_get: MagicMock, client) -> None:
        mock_mgr = MagicMock()
        mock_mgr.list_experiments.return_value = [
            ExperimentConfig(
                experiment_id="e1", workflow_name="wf1",
                prompt_id_a="p1", prompt_id_b="p2",
            ),
        ]
        mock_get.return_value = mock_mgr

        response = await client.get("/api/v1/prompts/experiments")
        assert response.status_code == 200
        assert len(response.json()) == 1

    @patch("app.api.v1.prompts.get_experiment_manager")
    async def test_create_experiment(self, mock_get: MagicMock, client) -> None:
        mock_mgr = MagicMock()
        mock_mgr.create_experiment.return_value = ExperimentConfig(
            experiment_id="e1", workflow_name="wf1",
            prompt_id_a="p1", prompt_id_b="p2",
            strategy=RolloutStrategy.SPLIT_50,
        )
        mock_get.return_value = mock_mgr

        response = await client.post(
            "/api/v1/prompts/experiments",
            json={
                "workflow_name": "wf1",
                "prompt_id_a": "p1",
                "prompt_id_b": "p2",
                "strategy": "split_50",
            },
        )
        assert response.status_code == 200
        assert response.json()["experiment_id"] == "e1"

    @patch("app.api.v1.prompts.get_experiment_manager")
    async def test_disable_experiment(self, mock_get: MagicMock, client) -> None:
        mock_mgr = MagicMock()
        mock_mgr.disable_experiment.return_value = True
        mock_get.return_value = mock_mgr

        response = await client.post("/api/v1/prompts/experiments/e1/disable")
        assert response.status_code == 200

    @patch("app.api.v1.prompts.get_experiment_manager")
    async def test_disable_experiment_not_found(self, mock_get: MagicMock, client) -> None:
        mock_mgr = MagicMock()
        mock_mgr.disable_experiment.return_value = False
        mock_get.return_value = mock_mgr

        response = await client.post("/api/v1/prompts/experiments/e1/disable")
        assert response.status_code == 404

    @patch("app.api.v1.prompts.get_all_dashboards")
    async def test_dashboard(self, mock_get: MagicMock, client) -> None:
        mock_get.return_value = [
            PromptDashboard(
                workflow_name="wf1",
                versions=[
                    PromptVersionMetrics(
                        prompt_id="p1", workflow_name="wf1", version=1,
                        usage_count=10, approval_rate=80.0,
                    ),
                ],
            ),
        ]

        response = await client.get("/api/v1/prompts/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["workflow_name"] == "wf1"
