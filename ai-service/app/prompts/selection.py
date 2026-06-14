from app.config.logging import get_logger
from app.prompts.registry import get_prompt_registry
from app.schemas.prompts import PromptVersion

logger = get_logger(__name__)


def select_prompt(
    workflow_name: str,
    version_override: int | None = None,
) -> tuple[PromptVersion | None, str]:
    registry = get_prompt_registry()

    if version_override is not None:
        version = registry.get_version_by_number(workflow_name, version_override)
        if version:
            logger.info("prompt_selected_override", workflow=workflow_name, version=version_override)
            return version, version.prompt_id
        logger.warning("prompt_override_not_found", workflow=workflow_name, version=version_override)

    active = registry.get_active(workflow_name)
    if active:
        logger.info("prompt_selected_active", workflow=workflow_name, version=active.version)
        return active, active.prompt_id

    logger.info("prompt_selected_default", workflow=workflow_name)
    return None, ""
