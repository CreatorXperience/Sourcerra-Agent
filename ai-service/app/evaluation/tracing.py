import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config.logging import get_logger
from app.config.settings import get_settings
from app.schemas.evaluation import WorkflowTrace

logger = get_logger(__name__)


class TracerStore:
    def __init__(self, store_path: str = ""):
        settings = get_settings()
        self._store_path = Path(store_path or settings.EVALUATION_STORE_PATH)
        self._store_path.mkdir(parents=True, exist_ok=True)
        self._traces_file = self._store_path / "traces.json"
        self._traces: list[WorkflowTrace] = []
        self._load()

    def start_trace(
        self,
        workflow_name: str,
        candidate_id: str,
        prompt_template: str = "",
        model_used: str = "",
        prompt_id: str = "",
        prompt_version: int = 0,
    ) -> str:
        run_id = str(uuid.uuid4())
        trace = WorkflowTrace(
            run_id=run_id,
            workflow_name=workflow_name,
            candidate_id=candidate_id,
            prompt_template=prompt_template,
            model_used=model_used,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            started_at=datetime.now(),
        )
        self._traces.append(trace)
        self._save()
        return run_id

    def complete_trace(
        self,
        run_id: str,
        output_snapshot: dict[str, Any] | None = None,
    ) -> None:
        for trace in self._traces:
            if trace.run_id == run_id:
                trace.completed_at = datetime.now()
                if output_snapshot:
                    trace.output_snapshot = output_snapshot
                self._save()
                return

    def get_trace(self, run_id: str) -> WorkflowTrace | None:
        for trace in self._traces:
            if trace.run_id == run_id:
                return trace
        return None

    def get_traces_by_workflow(self, workflow_name: str) -> list[WorkflowTrace]:
        return [t for t in self._traces if t.workflow_name == workflow_name]

    def get_traces_by_candidate(self, candidate_id: str) -> list[WorkflowTrace]:
        return [t for t in self._traces if t.candidate_id == candidate_id]

    def _save(self) -> None:
        try:
            data = [t.model_dump(mode="json") for t in self._traces]
            self._traces_file.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.warning("trace_store_save_failed", error=str(e))

    def _load(self) -> None:
        try:
            if self._traces_file.exists():
                data = json.loads(self._traces_file.read_text())
                self._traces = [WorkflowTrace(**item) for item in data]
                logger.info("trace_store_loaded", count=len(self._traces))
        except Exception as e:
            logger.warning("trace_store_load_failed", error=str(e))


_tracer_store: TracerStore | None = None


def get_tracer_store() -> TracerStore:
    global _tracer_store
    if _tracer_store is None:
        _tracer_store = TracerStore()
    return _tracer_store


class WorkflowTracer:
    def __init__(self, workflow_name: str, candidate_id: str):
        self.workflow_name = workflow_name
        self.candidate_id = candidate_id
        self.run_id: str = ""
        self.prompt_template: str = ""
        self.model_used: str = ""
        self.prompt_id: str = ""
        self.prompt_version: int = 0

    def start(self) -> str:
        store = get_tracer_store()
        self.run_id = store.start_trace(
            workflow_name=self.workflow_name,
            candidate_id=self.candidate_id,
            prompt_template=self.prompt_template,
            model_used=self.model_used,
            prompt_id=self.prompt_id,
            prompt_version=self.prompt_version,
        )
        return self.run_id

    def complete(self, output: dict[str, Any] | None = None) -> None:
        store = get_tracer_store()
        store.complete_trace(run_id=self.run_id, output_snapshot=output)
