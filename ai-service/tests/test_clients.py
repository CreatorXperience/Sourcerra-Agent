from app.clients.backend import BackendClient
from app.clients.ats import ATSService
from app.clients.auth import AuthService
from app.clients.resume import ResumeService
from app.config.settings import Settings


def test_backend_client_init() -> None:
    settings = Settings(BACKEND_API_BASE_URL="http://localhost:3000/api")
    client = BackendClient(settings)
    assert client.base_url == "http://localhost:3000/api"
    assert client.timeout == 30


def test_ats_service_init() -> None:
    settings = Settings()
    backend = BackendClient(settings)
    ats = ATSService(backend)
    assert ats._client is backend


def test_auth_service_init() -> None:
    settings = Settings()
    backend = BackendClient(settings)
    auth = AuthService(backend)
    assert auth._client is backend


def test_resume_service_init() -> None:
    settings = Settings()
    backend = BackendClient(settings)
    resume = ResumeService(backend)
    assert resume._client is backend
