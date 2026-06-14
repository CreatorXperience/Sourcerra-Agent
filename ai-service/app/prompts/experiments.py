import json
import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config.logging import get_logger
from app.schemas.prompts import ExperimentConfig, RolloutStrategy

logger = get_logger(__name__)


class ExperimentManager:
    def __init__(self, store_path: str = ""):
        from app.config.settings import get_settings
        settings = get_settings()
        self._store_path = Path(store_path or settings.EVALUATION_STORE_PATH)
        self._store_path.mkdir(parents=True, exist_ok=True)
        self._experiments_file = self._store_path / "experiments.json"
        self._experiments: list[ExperimentConfig] = []
        self._load()

    def create_experiment(
        self,
        workflow_name: str,
        prompt_id_a: str,
        prompt_id_b: str,
        strategy: RolloutStrategy = RolloutStrategy.FULL_A,
        weight_a: float = 1.0,
    ) -> ExperimentConfig:
        experiment = ExperimentConfig(
            experiment_id=str(uuid.uuid4()),
            workflow_name=workflow_name,
            prompt_id_a=prompt_id_a,
            prompt_id_b=prompt_id_b,
            strategy=strategy,
            weight_a=weight_a,
        )
        self._experiments.append(experiment)
        self._save()
        logger.info("experiment_created", workflow=workflow_name, strategy=strategy.value)
        return experiment

    def get_experiment(self, experiment_id: str) -> ExperimentConfig | None:
        for e in self._experiments:
            if e.experiment_id == experiment_id:
                return e
        return None

    def get_active_experiment(self, workflow_name: str) -> ExperimentConfig | None:
        for e in self._experiments:
            if e.workflow_name == workflow_name and e.enabled:
                return e
        return None

    def list_experiments(self, workflow_name: str | None = None) -> list[ExperimentConfig]:
        if workflow_name:
            return [e for e in self._experiments if e.workflow_name == workflow_name]
        return list(self._experiments)

    def disable_experiment(self, experiment_id: str) -> bool:
        for e in self._experiments:
            if e.experiment_id == experiment_id:
                e.enabled = False
                self._save()
                return True
        return False

    def assign(self, workflow_name: str, candidate_id: str) -> tuple[str, str, str]:
        experiment = self.get_active_experiment(workflow_name)
        if not experiment:
            from app.prompts.registry import get_prompt_registry
            active = get_prompt_registry().get_active(workflow_name)
            if active:
                return active.prompt_id, str(active.version), "default"
            return "", "0", "default"

        if experiment.strategy == RolloutStrategy.FULL_A:
            chosen = experiment.prompt_id_a
        elif experiment.strategy == RolloutStrategy.SPLIT_50:
            chosen = experiment.prompt_id_a if random.random() < 0.5 else experiment.prompt_id_b
        elif experiment.strategy == RolloutStrategy.WEIGHTED:
            chosen = experiment.prompt_id_a if random.random() < experiment.weight_a else experiment.prompt_id_b
        else:
            chosen = experiment.prompt_id_a

        from app.prompts.registry import get_prompt_registry
        version = get_prompt_registry().get_version(chosen)
        version_str = str(version.version) if version else "0"
        return chosen, version_str, experiment.experiment_id

    def _save(self) -> None:
        try:
            data = [e.model_dump(mode="json") for e in self._experiments]
            self._experiments_file.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.warning("experiment_save_failed", error=str(e))

    def _load(self) -> None:
        try:
            if self._experiments_file.exists():
                data = json.loads(self._experiments_file.read_text())
                self._experiments = [ExperimentConfig(**item) for item in data]
                logger.info("experiments_loaded", count=len(self._experiments))
        except Exception as e:
            logger.warning("experiment_load_failed", error=str(e))


_manager: ExperimentManager | None = None


def get_experiment_manager() -> ExperimentManager:
    global _manager
    if _manager is None:
        _manager = ExperimentManager()
    return _manager
