from fastapi.testclient import TestClient

from app.core.phi_scrubber import PHIScrubber
from app.main import app
from tests.unit._log_test_utils import (
    assert_any_string_contains,
    assert_no_string_contains,
    format_log_record,
)

REDACTED = PHIScrubber.REDACTED


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
        text = "tip title Hydrate Early description Drink water number 1"
        assert PHIScrubber().scrub_message(text) == text

    def test_leaves_business_id_untouched(self) -> None:
        assert PHIScrubber().scrub_message("tipId tip-001 ok") == "tipId tip-001 ok"


class TestTipsStructuredLogging:
    """The tips endpoint must emit machine-readable JSON with the request
    correlation context and no leaking credentials.
    """

    def test_tips_endpoint_emits_structured_json_with_request_context(
        self, json_log_records: list[dict[str, object]]
    ) -> None:
        with TestClient(app) as client:
            response = client.get(
                "/api/tips",
                headers={"X-Request-ID": "123e4567-e89b-12d3-a456-426614174000"},
            )
        assert response.status_code == 200

        record = next(
            (r for r in json_log_records if r.get("message") == "request.start"), None
        )
        assert record is not None
        assert record["requestId"] == "123e4567-e89b-12d3-a456-426614174000"
        assert record["method"] == "GET"
        assert record["path"] == "/api/tips"

    def test_credentials_scrubbed_in_tips_log_output(self) -> None:
        parsed = format_log_record("token=supersecret emitted during tips fetch")
        assert_no_string_contains(parsed, "supersecret")
        assert_any_string_contains(parsed, REDACTED)
