import json

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Sourcerra AI Service"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000

    # OpenRouter / OpenAI
    OPENAI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_DEFAULT_MODEL: str = "openai/gpt-4o"
    OPENROUTER_FALLBACK_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_MAX_RETRIES: int = 3
    OPENROUTER_TIMEOUT: int = 60

    # Backend API
    BACKEND_API_BASE_URL: str = "http://localhost:3000/api"
    BACKEND_API_KEY: str = ""
    BACKEND_API_TIMEOUT: int = 30

    # MCP
    # Stored as str (not list) to avoid pydantic-settings JSON decode failure on plain string env vars
    mcp_server_urls: str = Field(default="", alias="MCP_SERVER_URLS")
    MCP_CONNECTION_TIMEOUT: int = 10
    MCP_REQUEST_TIMEOUT: int = 60

    @property
    def MCP_SERVER_URLS(self) -> list[str]:
        raw = self.mcp_server_urls
        if not raw:
            return []
        if raw.startswith("["):
            return json.loads(raw)
        return [u.strip() for u in raw.split(",") if u.strip()]

    @model_validator(mode="before")
    @classmethod
    def _coerce_mcp_urls(cls, data: dict) -> dict:
        raw = data.get("MCP_SERVER_URLS")
        if isinstance(raw, list | tuple):
            data["MCP_SERVER_URLS"] = ",".join(raw)
        return data

    # Agents
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_DEFAULT_MODEL: str = ""
    AGENT_ENABLE_HANDOFFS: bool = True
    AGENT_ENABLE_GUARDRAILS: bool = True

    # Storage
    PROMPT_STORE_PATH: str = "data/evaluation"
    EVALUATION_STORE_PATH: str = "data/evaluation"

    # Database (optional)
    DATABASE_URL: str = ""

    # Redis (optional)
    REDIS_URL: str = ""

    # Security
    API_KEY: str = ""
    CORS_ORIGINS: str = "*"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

    # Observability
    OTEL_ENABLED: bool = False
    OTEL_SERVICE_NAME: str = "sourcerra-ai"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4318"

    # Feature Flags
    PROMPT_VERSIONING_ENABLED: bool = True
    EVALUATION_ENABLED: bool = True
    TRACING_ENABLED: bool = True

    @model_validator(mode="after")
    def validate_provider(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            if not self.OPENROUTER_API_KEY and not self.OPENAI_API_KEY:
                raise ValueError(
                    "OPENROUTER_API_KEY or OPENAI_API_KEY must be set in production"
                )
        return self


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
