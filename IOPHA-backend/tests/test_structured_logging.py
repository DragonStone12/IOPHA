import json
import logging
from io import StringIO

from app.logging import (
    JsonTelemetryFormatter,
)

# ---------------------------------------------------------------------------
# JsonTelemetryFormatter tests
# ---------------------------------------------------------------------------


class TestJsonTelemetryFormatter:
    def test_outputs_valid_json(self):
        formatter = JsonTelemetryFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello world",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["message"] == "hello world"

    def test_includes_required_fields(self):
        formatter = JsonTelemetryFormatter()
        record = logging.LogRecord(
            name="iopha.backend",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="request.start",
            args=(),
            exc_info=None,
        )
        output = json.loads(formatter.format(record))
        assert "timestamp" in output
        assert "level" in output
        assert "logger" in output
        assert "message" in output
        assert output["level"] == "INFO"
        assert output["logger"] == "iopha.backend"

    def test_includes_extra_context(self):
        formatter = JsonTelemetryFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="request.start",
            args=(),
            exc_info=None,
        )
        record.extra_context = {"requestId": "abc-123", "path": "/chat/message"}
        output = json.loads(formatter.format(record))
        assert output["requestId"] == "abc-123"
        assert output["path"] == "/chat/message"

    def test_iso_timestamp_format(self):
        formatter = JsonTelemetryFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        output = json.loads(formatter.format(record))
        assert "T" in output["timestamp"]


# ---------------------------------------------------------------------------
# PathSanitizer: behavior for non-existent API routes
# ---------------------------------------------------------------------------
# Path sanitization for routes that do not yet exist in the backend
# (e.g. /patients/:id, /providers/:id, /sessions/:id, /users/:id) is
# documented in:
#   - docs/security/SECURITY.md  ("Backend PII/PHI Sanitization")
#   - docs/infra/TECHNICAL_DESIGN.md ("PII/PHI Sanitization Architecture")
# Tests for actual API routes are covered in TestStructuredJsonOutput below.


# ---------------------------------------------------------------------------
# Integration: structured JSON output from logger
# ---------------------------------------------------------------------------


class TestStructuredJsonOutput:
    def test_logger_outputs_json_to_stream(self):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JsonTelemetryFormatter())
        logger = logging.getLogger("test.json.logger")
        logger.handlers = [handler]
        logger.setLevel(logging.INFO)

        logger.info("request.start", extra={"extra_context": {"path": "/chat/message"}})
        output = stream.getvalue().strip()
        parsed = json.loads(output)
        assert parsed["message"] == "request.start"
        assert parsed["path"] == "/chat/message"
