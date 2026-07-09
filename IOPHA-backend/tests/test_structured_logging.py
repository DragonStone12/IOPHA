import json
import logging

from fastapi.testclient import TestClient

from app.logging import JsonTelemetryFormatter
from app.main import app

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
# CentralizedLoggingMiddleware smoke tests
# ---------------------------------------------------------------------------


class TestCentralizedLoggingMiddleware:
    def test_logs_request_start_and_complete(self):
        client = TestClient(app)
        response = client.get("/metrics")
        assert response.status_code in (200, 404)

    def test_logs_request_for_non_existent_route(self):
        client = TestClient(app)
        response = client.get("/non-existent-route")
        assert response.status_code == 404
