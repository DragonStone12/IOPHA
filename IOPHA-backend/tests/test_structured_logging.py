import json
import logging
from io import StringIO

from app.logging import (
    JsonTelemetryFormatter,
    PathSanitizer,
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
        record.extra_context = {"requestId": "abc-123", "path": "/patients/:id"}
        output = json.loads(formatter.format(record))
        assert output["requestId"] == "abc-123"
        assert output["path"] == "/patients/:id"

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
# PathSanitizer tests
# ---------------------------------------------------------------------------


class TestPathSanitizer:
    def test_sanitizes_patient_paths(self):
        assert PathSanitizer.sanitize_path("/patients/12345") == "/patients/:id"
        assert PathSanitizer.sanitize_path("/patients/0") == "/patients/:id"

    def test_sanitizes_provider_paths(self):
        assert PathSanitizer.sanitize_path("/providers/999") == "/providers/:id"

    def test_sanitizes_session_paths(self):
        assert PathSanitizer.sanitize_path("/sessions/42") == "/sessions/:id"

    def test_sanitizes_user_paths(self):
        assert PathSanitizer.sanitize_path("/users/7") == "/users/:id"

    def test_leaves_plain_paths_unchanged(self):
        assert PathSanitizer.sanitize_path("/status") == "/status"
        assert PathSanitizer.sanitize_path("/docs") == "/docs"

    def test_sanitizes_multiple_segments(self):
        result = PathSanitizer.sanitize_path("/patients/123/records/456")
        assert result == "/patients/:id/records/456"

    def test_redacts_sensitive_query_params(self):
        query = {
            "email": "test@example.com",
            "phone": "555-123-4567",
            "specialty": "cardiology",
        }
        sanitized = PathSanitizer.sanitize_query(query)
        assert sanitized["email"] == "[REDACTED]"
        assert sanitized["phone"] == "[REDACTED]"
        assert sanitized["specialty"] == "cardiology"

    def test_query_keys_case_insensitive(self):
        query = {"EMAIL": "test@example.com", "Phone": "555-123-4567"}
        sanitized = PathSanitizer.sanitize_query(query)
        assert sanitized["EMAIL"] == "[REDACTED]"
        assert sanitized["Phone"] == "[REDACTED]"

    def test_mask_user_id_truncates(self):
        assert PathSanitizer.mask_user_id("user_123456") == "user_***456"

    def test_mask_user_id_short_becomes_redacted(self):
        assert PathSanitizer.mask_user_id("user_12") == "[REDACTED_USER]"

    def test_mask_user_id_unknown_becomes_redacted(self):
        assert PathSanitizer.mask_user_id("unknown") == "[REDACTED_USER]"


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

        logger.info("request.start", extra={"extra_context": {"path": "/patients/:id"}})
        output = stream.getvalue().strip()
        parsed = json.loads(output)
        assert parsed["message"] == "request.start"
        assert parsed["path"] == "/patients/:id"
