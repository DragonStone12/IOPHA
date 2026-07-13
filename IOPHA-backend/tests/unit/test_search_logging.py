import json
import logging

from fastapi.testclient import TestClient

from app.core.context import request_id_ctx
from app.core.logging_config import JSONLogFormatter
from app.core.phi_scrubber import PHIScrubber
from app.main import app

REDACTED = PHIScrubber.REDACTED


def _format(msg: str, extra: dict[str, object] | None = None) -> dict[str, object]:
    rec = logging.LogRecord(
        name="iopha.backend",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=None,
    )
    if extra is not None:
        rec.extra_context = extra
    return json.loads(JSONLogFormatter().format(rec))


class TestSearchStructuredLogging:
    """The search endpoint must emit machine-readable JSON with the request
    correlation context and no leaking credentials.
    """

    def test_search_request_log_is_valid_json_with_request_context(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/providers/search",
                json={"queryText": "Cardiologist"},
                headers={"X-Request-ID": "trace-search-1"},
            )
        assert response.status_code == 200
        token = request_id_ctx.set("trace-search-1")
        try:
            parsed = _format(
                "request.start",
                {"method": "POST", "path": "/api/v1/providers/search"},
            )
        finally:
            request_id_ctx.reset(token)

        assert parsed["requestId"] == "trace-search-1"
        assert parsed["method"] == "POST"
        assert parsed["path"] == "/api/v1/providers/search"
        assert json.loads(json.dumps(parsed)) == parsed

    def test_credentials_scrubbed_in_search_log_output(self) -> None:
        parsed = _format("api_key=supersecret emitted during search fetch")
        assert "supersecret" not in parsed
        _assert_any_string_contains(parsed, REDACTED)


def _assert_any_string_contains(value: object, expected: str) -> None:
    found = False

    def _walk(v: object) -> None:
        nonlocal found
        if found:
            return
        if isinstance(v, str):
            if expected in v:
                found = True
        elif isinstance(v, dict):
            for val in v.values():
                _walk(val)
        elif isinstance(v, (list, tuple)):
            for item in v:
                _walk(item)

    _walk(value)
    assert found, f"Expected substring {expected!r} not found in any string"
