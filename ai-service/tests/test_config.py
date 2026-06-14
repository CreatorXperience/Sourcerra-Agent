from app.config.settings import Settings, get_settings


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.APP_NAME == "Sourcerra AI Service"
    assert settings.DEBUG is False
    assert settings.LOG_LEVEL == "INFO"
    assert settings.OPENROUTER_BASE_URL == "https://openrouter.ai/api/v1"
    assert settings.BACKEND_API_BASE_URL == "http://localhost:3000/api"
    assert settings.MCP_SERVER_URLS == []


def test_settings_env_override() -> None:
    settings = Settings(
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        OPENROUTER_API_KEY="test-key-123",
    )
    assert settings.DEBUG is True
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.OPENROUTER_API_KEY == "test-key-123"


def test_get_settings_singleton() -> None:
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
