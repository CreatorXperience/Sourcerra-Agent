from abc import ABC, abstractmethod
from typing import Any

from app.schemas.models import ModelConfig


class BaseLLMProvider(ABC):
    @abstractmethod
    async def chat_completion(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...

    @abstractmethod
    def get_model_config(self, model_id: str) -> ModelConfig:
        ...
