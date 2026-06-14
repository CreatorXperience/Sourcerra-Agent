import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config.logging import get_logger
from app.config.settings import get_settings
from app.schemas.evaluation import (
    FeedbackRating,
    FeedbackRecord,
    FeedbackStats,
    WorkflowMetrics,
)

logger = get_logger(__name__)


class FeedbackStore:
    def __init__(self, store_path: str = ""):
        settings = get_settings()
        self._store_path = Path(store_path or settings.EVALUATION_STORE_PATH)
        self._store_path.mkdir(parents=True, exist_ok=True)
        self._feedback_file = self._store_path / "feedback.json"
        self._records: list[FeedbackRecord] = []
        self._load()

    def add_feedback(
        self,
        workflow_name: str,
        candidate_id: str,
        rating: FeedbackRating,
        feedback_text: str = "",
        prompt_template: str = "",
        model_used: str = "",
    ) -> FeedbackRecord:
        record = FeedbackRecord(
            id=str(uuid.uuid4()),
            workflow_name=workflow_name,
            candidate_id=candidate_id,
            rating=rating,
            feedback_text=feedback_text,
            timestamp=datetime.now(),
            prompt_template=prompt_template,
            model_used=model_used,
        )
        self._records.append(record)
        self._save()
        logger.info("feedback_recorded", id=record.id, workflow=workflow_name, rating=rating.value)
        return record

    def get_all_feedback(self) -> list[FeedbackRecord]:
        return list(self._records)

    def get_feedback_by_workflow(self, workflow_name: str) -> list[FeedbackRecord]:
        return [r for r in self._records if r.workflow_name == workflow_name]

    def get_feedback_by_candidate(self, candidate_id: str) -> list[FeedbackRecord]:
        return [r for r in self._records if r.candidate_id == candidate_id]

    def get_stats(self) -> FeedbackStats:
        total = len(self._records)
        if total == 0:
            return FeedbackStats()

        approvals = sum(1 for r in self._records if r.rating == FeedbackRating.UP)
        rejections = sum(1 for r in self._records if r.rating == FeedbackRating.DOWN)

        usage: dict[str, int] = {}
        for r in self._records:
            usage[r.workflow_name] = usage.get(r.workflow_name, 0) + 1

        metrics_list: list[WorkflowMetrics] = []
        for wf_name, count in usage.items():
            wf_records = [r for r in self._records if r.workflow_name == wf_name]
            wf_approvals = sum(1 for r in wf_records if r.rating == FeedbackRating.UP)
            wf_rejections = count - wf_approvals
            metrics_list.append(WorkflowMetrics(
                workflow_name=wf_name,
                total=count,
                approvals=wf_approvals,
                rejections=wf_rejections,
                approval_rate=round(wf_approvals / count * 100, 1) if count else 0.0,
            ))

        return FeedbackStats(
            total_feedback=total,
            approval_rate=round(approvals / total * 100, 1),
            rejection_rate=round(rejections / total * 100, 1),
            workflow_usage=usage,
            workflow_metrics=metrics_list,
        )

    def _save(self) -> None:
        try:
            data = [r.model_dump(mode="json") for r in self._records]
            self._feedback_file.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.warning("feedback_store_save_failed", error=str(e))

    def _load(self) -> None:
        try:
            if self._feedback_file.exists():
                data = json.loads(self._feedback_file.read_text())
                self._records = [FeedbackRecord(**item) for item in data]
                logger.info("feedback_store_loaded", count=len(self._records))
        except Exception as e:
            logger.warning("feedback_store_load_failed", error=str(e))


_store: FeedbackStore | None = None


def get_feedback_store() -> FeedbackStore:
    global _store
    if _store is None:
        _store = FeedbackStore()
    return _store
