from typing import Any

from openai import AsyncOpenAI

from app.config.logging import get_logger
from app.config.settings import Settings
from app.providers.base import BaseLLMProvider
from app.schemas.models import ModelConfig, ModelProvider

logger = get_logger(__name__)


class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = self._create_client()
        self._default_model = settings.OPENROUTER_DEFAULT_MODEL
        self._fallback_model = settings.OPENROUTER_FALLBACK_MODEL
        self._max_retries = settings.OPENROUTER_MAX_RETRIES
        self._timeout = settings.OPENROUTER_TIMEOUT

    def _create_client(self) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=self.settings.OPENROUTER_API_KEY,
            base_url=self.settings.OPENROUTER_BASE_URL,
        )

    async def chat_completion(
        self,
        model: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        model = model or self._default_model
        messages = messages or []

        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            **kwargs,
        }

        if tools:
            params["tools"] = tools

        response = await self.client.chat.completions.create(**params)
        return response.model_dump()

    async def is_available(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False

    def get_model_config(self, model_id: str) -> ModelConfig:
        return ModelConfig(
            id=model_id,
            provider=ModelProvider.OPENAI,
            display_name=model_id,
        )

    async def close(self) -> None:
        await self.client.close()
