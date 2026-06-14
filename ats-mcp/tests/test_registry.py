from app.tools.registry import ToolRegistry, get_registry
from app.core.errors import NotFoundError, BackendConnectionError, BackendResponseError, tool_error_to_content


def test_tool_registry_singleton() -> None:
    r1 = get_registry()
    r2 = get_registry()
    assert r1 is r2


def test_tool_registry_register_and_list() -> None:
    registry = ToolRegistry()
    assert registry.count == 0

    async def fake_handler(args):
        return [{"type": "text", "text": "ok"}], False

    registry.register(
        name="ats_get_candidate",
        description="Get a candidate",
        handler=fake_handler,
        input_schema={"type": "object", "properties": {}},
    )
    assert registry.count == 1

    definitions = registry.list_definitions()
    assert len(definitions) == 1
    assert definitions[0].name == "ats_get_candidate"

    handler = registry.get_handler("ats_get_candidate")
    assert handler is fake_handler

    unknown = registry.get_handler("nonexistent")
    assert unknown is None


class TestErrors:
    def test_not_found_error(self) -> None:
        err = NotFoundError("Candidate", "cand-123")
        assert err.code == "NOT_FOUND"
        assert "cand-123" in err.message

        resp = err.to_response()
        assert resp.error.code == "NOT_FOUND"

    def test_backend_connection_error(self) -> None:
        err = BackendConnectionError("Connection refused")
        assert err.code == "BACKEND_CONNECTION_ERROR"

    def test_backend_response_error(self) -> None:
        err = BackendResponseError(500, "Internal server error")
        assert err.code == "BACKEND_RESPONSE_ERROR"

    def test_tool_error_to_content(self) -> None:
        err = NotFoundError("Job", "job-1")
        content, is_error = tool_error_to_content(err)
        assert is_error is True
        assert "not found" in content[0]["text"].lower()
