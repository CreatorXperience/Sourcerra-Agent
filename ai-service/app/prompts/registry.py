import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config.logging import get_logger
from app.schemas.prompts import PromptStatus, PromptVersion

logger = get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent


class PromptRegistry:
    def __init__(self, store_path: str = ""):
        from app.config.settings import get_settings
        settings = get_settings()
        self._store_path = Path(store_path or settings.EVALUATION_STORE_PATH)
        self._store_path.mkdir(parents=True, exist_ok=True)
        self._registry_file = self._store_path / "prompt_registry.json"
        self._versions: list[PromptVersion] = []
        self._load()

    def register(self, workflow_name: str, content: str) -> PromptVersion:
        existing = [v for v in self._versions if v.workflow_name == workflow_name]
        next_version = max((v.version for v in existing), default=0) + 1
        prompt = PromptVersion(
            prompt_id=str(uuid.uuid4()),
            workflow_name=workflow_name,
            version=next_version,
            status=PromptStatus.DRAFT,
            content=content,
        )
        self._versions.append(prompt)
        self._save()
        logger.info("prompt_registered", workflow=workflow_name, version=next_version)
        return prompt

    def activate(self, prompt_id: str) -> PromptVersion | None:
        for v in self._versions:
            if v.prompt_id == prompt_id:
                for other in self._versions:
                    if other.workflow_name == v.workflow_name and other.status == PromptStatus.ACTIVE:
                        other.status = PromptStatus.ARCHIVED
                v.status = PromptStatus.ACTIVE
                v.updated_at = datetime.now()
                self._save()
                logger.info("prompt_activated", workflow=v.workflow_name, version=v.version)
                return v
        return None

    def archive(self, prompt_id: str) -> PromptVersion | None:
        for v in self._versions:
            if v.prompt_id == prompt_id:
                v.status = PromptStatus.ARCHIVED
                v.updated_at = datetime.now()
                self._save()
                return v
        return None

    def get_active(self, workflow_name: str) -> PromptVersion | None:
        for v in self._versions:
            if v.workflow_name == workflow_name and v.status == PromptStatus.ACTIVE:
                return v
        return None

    def get_version(self, prompt_id: str) -> PromptVersion | None:
        for v in self._versions:
            if v.prompt_id == prompt_id:
                return v
        return None

    def get_version_by_number(self, workflow_name: str, version: int) -> PromptVersion | None:
        for v in self._versions:
            if v.workflow_name == workflow_name and v.version == version:
                return v
        return None

    def list_versions(self, workflow_name: str | None = None) -> list[PromptVersion]:
        if workflow_name:
            return [v for v in self._versions if v.workflow_name == workflow_name]
        return list(self._versions)

    def _save(self) -> None:
        try:
            data = [v.model_dump(mode="json") for v in self._versions]
            self._registry_file.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.warning("prompt_registry_save_failed", error=str(e))

    def _load(self) -> None:
        try:
            if self._registry_file.exists():
                data = json.loads(self._registry_file.read_text())
                self._versions = [PromptVersion(**item) for item in data]
                logger.info("prompt_registry_loaded", count=len(self._versions))
        except Exception as e:
            logger.warning("prompt_registry_load_failed", error=str(e))


_registry: PromptRegistry | None = None


def get_prompt_registry() -> PromptRegistry:
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
    return _registry
