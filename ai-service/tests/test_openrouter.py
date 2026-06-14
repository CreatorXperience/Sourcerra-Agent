
from app.config.settings import Settings
from app.providers.openrouter import OpenRouterProvider
from app.schemas.models import ModelConfig, ModelProvider


def test_openrouter_provider_initialization() -> None:
    settings = Settings(OPENROUTER_API_KEY="test-key")
    provider = OpenRouterProvider(settings)
    assert provider._default_model == settings.OPENROUTER_DEFAULT_MODEL
    assert provider._fallback_model == settings.OPENROUTER_FALLBACK_MODEL


def test_openrouter_get_model_config() -> None:
    settings = Settings(OPENROUTER_API_KEY="test-key")
    provider = OpenRouterProvider(settings)
    config = provider.get_model_config("openai/gpt-4o")
    assert isinstance(config, ModelConfig)
    assert config.id == "openai/gpt-4o"
    assert config.provider == ModelProvider.OPENAI
