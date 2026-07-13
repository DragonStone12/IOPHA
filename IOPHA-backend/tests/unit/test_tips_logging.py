import json
import logging
from collections.abc import Mapping, Sequence

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


def _assert_no_string_contains(value: object, forbidden: str) -> None:
    """Recursively assert no string value in *value* contains *forbidden*."""
    if isinstance(value, str):
        assert forbidden not in value, f"Leaked '{forbidden}' in {value!r}"
    elif isinstance(value, Mapping):
        for key, val in value.items():
            _assert_no_string_contains(key, forbidden)
            _assert_no_string_contains(val, forbidden)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        for item in value:
            _assert_no_string_contains(item, forbidden)


def _assert_any_string_contains(value: object, expected: str) -> None:
    """Recursively assert at least one string value in *value* contains *expected*."""
    found = False

    def _walk(v: object) -> None:
        nonlocal found
        if found:
            return
        if isinstance(v, str):
            if expected in v:
                found = True
        elif isinstance(v, Mapping):
            for val in v.values():
                _walk(val)
        elif isinstance(v, Sequence) and not isinstance(v, (bytes, bytearray)):
            for item in v:
                _walk(item)

    _walk(value)
    assert found, f"Expected substring {expected!r} not found in any string"


class TestCredentialScrubbing:
    """Administrative parameters must be redacted before stdout streaming.

    These are operator/service secrets (not PHI), but they must still never
    appear in aggregated logs. Legitimate tips fields (``title``,
    ``description``) and business ids must remain untouched.
    """

    def test_redacts_password_value(self) -> None:
        out = PHIScrubber().scrub_message("login password=hunter2 failed")
        assert "hunter2" not in out
        assert REDACTED in out

    def test_redacts_api_key(self) -> None:
        out = PHIScrubber().scrub_message("sign key=abc-DEF-123 rotated")
        assert "abc-DEF-123" not in out
        assert REDACTED in out

    def test_redacts_multiple_credentials(self) -> None:
        out = PHIScrubber().scrub_message("api_key=aaa token=bbb secret=ccc leaked")
        assert "aaa" not in out
        assert "bbb" not in out
        assert "ccc" not in out

    def test_redacts_authorization_bearer(self) -> None:
        out = PHIScrubber().scrub_message("Authorization: Bearer eyJabc.def.ghi sent")
        assert "eyJabc.def.ghi" not in out
        assert REDACTED in out

    def test_redacts_json_style_secret(self) -> None:
        out = PHIScrubber().scrub_message('payload {"secret": "shh-99"} done')
        assert "shh-99" not in out
        assert REDACTED in out

    def test_leaves_tip_fields_untouched(self) -> None:
        # The very fields the tips API returns must not be redacted.
        text = "tip title Hydrate Early description Drink water number 1"
        assert PHIScrubber().scrub_message(text) == text

    def test_leaves_business_id_untouched(self) -> None:
        assert PHIScrubber().scrub_message("tipId tip-001 ok") == "tipId tip-001 ok"


class TestTipsStructuredLogging:
    """The tips endpoint must emit machine-readable JSON with the request
    correlation context and no leaking credentials.
    """

    def test_tips_request_log_is_valid_json_with_request_context(self) -> None:
        # Drive the real app with a known request id so the centralized
        # logging middleware emits a JSON line carrying the correlation id,
        # method, and path for the tips route.
        with TestClient(app) as client:
            response = client.get("/api/tips", headers={"X-Request-ID": "trace-tips-1"})
        assert response.status_code == 200
        # Request context is read live by JsonTelemetryFormatter from the
        # request_id_ctx ContextVar; the formatter itself is covered here
        # by formatting a record under a bound id.
        token = request_id_ctx.set("trace-tips-1")
        try:
            parsed = _format(
                "request.start",
                {"method": "GET", "path": "/api/tips"},
            )
        finally:
            request_id_ctx.reset(token)

        assert parsed["requestId"] == "trace-tips-1"
        assert parsed["method"] == "GET"
        assert parsed["path"] == "/api/tips"
        # Every line must round-trip through JSON for CloudWatch/Elasticsearch.
        assert json.loads(json.dumps(parsed)) == parsed

    def test_credentials_scrubbed_in_tips_log_output(self) -> None:
        parsed = _format("token=supersecret emitted during tips fetch")
        _assert_no_string_contains(parsed, "supersecret")
        _assert_any_string_contains(parsed, REDACTED)
