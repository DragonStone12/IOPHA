from fastapi.testclient import TestClient

from app.core.phi_scrubber import PHIScrubber
from app.main import app
from tests.unit._log_test_utils import (
    assert_any_string_contains,
    assert_no_string_contains,
    format_log_record,
)

REDACTED = PHIScrubber.REDACTED


class TestSearchStructuredLogging:
    """The search endpoint must emit machine-readable JSON with the request
    correlation context and no leaking credentials.
    """

    def test_search_endpoint_emits_structured_json_with_request_context(
        self, json_log_records: list[dict[str, object]]
    ) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/providers/search",
                json={"queryText": "Cardiologist"},
                headers={"X-Request-ID": "123e4567-e89b-12d3-a456-426614174000"},
            )
        assert response.status_code == 200

        record = next(
            (r for r in json_log_records if r.get("message") == "request.start"), None
        )
        assert record is not None
        assert record["requestId"] == "123e4567-e89b-12d3-a456-426614174000"
        assert record["method"] == "POST"
        assert record["path"] == "/api/providers/search"

    def test_credentials_scrubbed_in_search_log_output(self) -> None:
        parsed = format_log_record("api_key=supersecret emitted during search fetch")
        assert_no_string_contains(parsed, "supersecret")
        assert_any_string_contains(parsed, REDACTED)
