from fastapi.testclient import TestClient

from app.main import app


class TestTimeSlotEndpointSmoke:
    def test_returns_200_with_slots(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/providers/prov-123/slots")
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) > 0
        slot = body[0]
        assert set(slot.keys()) == {"id", "time", "label", "available"}
        # Matches the frontend TimeSlot contract.
        assert slot["id"].endswith(slot["time"])

    def test_unknown_provider_returns_empty_list(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/providers/does-not-exist/slots")
        assert response.status_code == 200
        assert response.json() == []

    def test_openapi_documents_response_model(self) -> None:
        spec = app.openapi()
        path = spec["paths"]["/api/providers/{provider_id}/slots"]
        assert "get" in path
        assert path["get"]["responses"]["200"]["content"]["application/json"]["schema"][
            "$ref"
        ].endswith("TimeSlotSchema")
