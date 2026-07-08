import json
import logging

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
