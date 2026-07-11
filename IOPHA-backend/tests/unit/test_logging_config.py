import json
import logging

from app.core.context import request_id_ctx
from app.core.logging_config import JSONLogFormatter


def _record(msg: str, extra: dict[str, object] | None = None) -> logging.LogRecord:
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
    return rec


class TestJSONLogFormatter:
    def test_outputs_valid_json(self) -> None:
        out = JSONLogFormatter().format(_record("hello world"))
        parsed = json.loads(out)
        assert parsed["message"] == "hello world"

    def test_includes_required_fields(self) -> None:
        parsed = json.loads(JSONLogFormatter().format(_record("request.start")))
        for field in ("timestamp", "level", "requestId", "message"):
            assert field in parsed
        assert parsed["level"] == "INFO"

    def test_includes_method_and_path_from_context(self) -> None:
        parsed = json.loads(
            JSONLogFormatter().format(
                _record(
                    "request.start",
                    {"method": "GET", "path": "/api/providers/1/slots"},
                )
            )
        )
        assert parsed["method"] == "GET"
        assert parsed["path"] == "/api/providers/1/slots"

    def test_request_id_pulled_from_context(self) -> None:
        token = request_id_ctx.set("trace-7")
        try:
            parsed = json.loads(JSONLogFormatter().format(_record("x")))
            assert parsed["requestId"] == "trace-7"
        finally:
            request_id_ctx.reset(token)

    def test_phi_scrubbed_in_message(self) -> None:
        out = JSONLogFormatter().format(_record("email john@x.com phone 555-123-4567"))
        assert "john@x.com" not in out
        assert "555-123-4567" not in out
        assert "[REDACTED]" in out

    def test_phi_scrubbed_in_extra_context(self) -> None:
        # Names appear in logs alongside a recognizable label, not bare.
        out = JSONLogFormatter().format(
            _record("x", {"note": "patient: Jane Doe scheduled"})
        )
        assert "Jane Doe" not in out
        assert "[REDACTED]" in out
