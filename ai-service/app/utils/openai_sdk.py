
from openai import AsyncOpenAI

from app.config.logging import get_logger
from app.config.settings import Settings

logger = get_logger(__name__)


class OpenAISDKWrapper:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
        )

    @property
    def default_model(self) -> str:
        return self.settings.OPENROUTER_DEFAULT_MODEL

    @property
    def fallback_model(self) -> str:
        return self.settings.OPENROUTER_FALLBACK_MODEL

    async def close(self) -> None:
        await self.client.close()
