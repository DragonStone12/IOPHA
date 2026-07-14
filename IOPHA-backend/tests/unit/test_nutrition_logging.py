from fastapi.testclient import TestClient

from app.main import app


class TestNutritionStructuredLogging:
    """The nutrition endpoint must emit machine-readable JSON with the
    request correlation context and no leaking credentials/identifiers.
    """

    def test_nutrition_endpoint_emits_structured_json_with_request_context(
        self, json_log_records: list[dict[str, object]]
    ) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/nutrition/evaluate",
                json={"profileId": "valid-profile"},
                headers={"X-Request-ID": "123e4567-e89b-12d3-a456-426614174000"},
            )
        assert response.status_code == 200

        record = next(
            (r for r in json_log_records if r.get("message") == "nutrition.evaluate"),
            None,
        )
        assert record is not None
        # The sync endpoint runs in a threadpool; the request_id_ctx
        # must still be inherited so the log correlates to the inbound
        # X-Request-ID header (HIPAA-traceable, no patient id).
        assert record["requestId"] == ("123e4567-e89b-12d3-a456-426614174000")
        # profileId must NOT appear in the log payload (HIPAA
        # minimum-necessary: never log a patient/profile identifier).
        assert "profileId" not in record
