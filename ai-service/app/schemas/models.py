from enum import Enum

from pydantic import BaseModel


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MISTRAL = "mistral"
    META = "meta"
    DEEPSEEK = "deepseek"


class ModelRoute(BaseModel):
    model_id: str
    provider: ModelProvider
    weight: int = 1
    fallback: str | None = None


class OpenRouterConfig(BaseModel):
    api_key: str = ""
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "openai/gpt-4o"
    fallback_model: str = "openai/gpt-4o-mini"
    max_retries: int = 3
    timeout: int = 60


class ModelConfig(BaseModel):
    id: str
    provider: ModelProvider
    display_name: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    supports_structured_output: bool = False
    supports_function_calling: bool = True
    supports_vision: bool = False
