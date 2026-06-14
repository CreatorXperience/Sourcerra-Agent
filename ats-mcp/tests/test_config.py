from app.config import Settings, get_settings


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.APP_NAME == "ATS MCP Server"
    assert settings.DEBUG is False
    assert settings.LOG_LEVEL == "INFO"
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8001
    assert settings.BACKEND_API_BASE_URL == "http://localhost:3000/api"
    assert settings.BACKEND_API_KEY == ""
    assert settings.BACKEND_API_TIMEOUT == 30


def test_settings_env_override() -> None:
    settings = Settings(
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        BACKEND_API_BASE_URL="http://api.example.com",
        BACKEND_API_KEY="mcp-key-123",
    )
    assert settings.DEBUG is True
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.BACKEND_API_BASE_URL == "http://api.example.com"
    assert settings.BACKEND_API_KEY == "mcp-key-123"


def test_get_settings_singleton() -> None:
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
