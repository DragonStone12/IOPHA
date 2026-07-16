from datetime import date

from fastapi.testclient import TestClient

from app.main import app


class TestTimeSlotEndpointSmoke:
    def test_returns_200_with_slots(self) -> None:
        query_date = date.today().isoformat()
        with TestClient(app) as client:
            response = client.get(f"/api/providers/prov-123/slots?date={query_date}")
        assert response.status_code == 200
        body = response.json()
        assert "date" in body
        assert "slots" in body
        assert isinstance(body["slots"], list)
        assert len(body["slots"]) > 0
        slot = body["slots"][0]
        assert set(slot.keys()) == {"id", "time", "label", "available"}
        # Matches the frontend TimeSlot contract.
        assert slot["id"].endswith(slot["time"])

    def test_unknown_provider_returns_404(self) -> None:
        query_date = date.today().isoformat()
        with TestClient(app) as client:
            response = client.get(
                f"/api/providers/does-not-exist/slots?date={query_date}"
            )
        assert response.status_code == 404
        body = response.json()
        assert body["title"] == "Provider Not Found"
        assert body["status"] == 404

    def test_missing_date_returns_422(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/providers/prov-123/slots")
        assert response.status_code == 422
        body = response.json()
        assert body["title"] == "Unprocessable Entity"

    def test_openapi_documents_response_model(self) -> None:
        spec = app.openapi()
        path = spec["paths"]["/api/providers/{provider_id}/slots"]
        assert "get" in path
        schema = path["get"]["responses"]["200"]["content"]["application/json"][
            "schema"
        ]
        assert schema["$ref"].endswith("CalendarSlotsResponseSchema")
