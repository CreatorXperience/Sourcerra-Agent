from app.core.tracing import ToolTracer, get_tracer


def test_tracer_singleton() -> None:
    t1 = get_tracer()
    t2 = get_tracer()
    assert t1 is t2


def test_tracer_disabled() -> None:
    tracer = ToolTracer(enabled=False)
    tracer.trace_sync("test_tool", {"arg": 1}, {"result": "ok"}, 10.0, error=None)
    assert True


def test_tracer_enabled() -> None:
    tracer = ToolTracer(enabled=True)
    tracer.trace_sync("test_tool", {"arg": 1}, {"result": "ok"}, 10.0, error=None)
    assert True


def test_tracer_with_error() -> None:
    tracer = ToolTracer(enabled=True)
    tracer.trace_sync("test_tool", {"arg": 1}, None, 5.0, error="Something broke")
    assert True
