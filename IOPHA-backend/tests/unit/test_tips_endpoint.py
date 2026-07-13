from fastapi.testclient import TestClient

from app.main import app


class TestTipsEndpointSmoke:
    def test_returns_200_with_tips(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/tips")
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) > 0
        tip = body[0]
        assert set(tip.keys()) == {"id", "number", "title", "description"}
        # Matches the frontend Tip contract (id?, number, title, description).
        assert isinstance(tip["number"], int)
        assert tip["number"] >= 1

    def test_tips_are_ordered_by_number(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/tips")
        numbers = [tip["number"] for tip in response.json()]
        assert numbers == sorted(numbers)

    def test_limit_query_parameter_caps_results(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/tips", params={"limit": 1})
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1

    def test_invalid_limit_returns_422_problem(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/tips", params={"limit": 0})
        assert response.status_code == 422
        body = response.json()
        # Projected into the RFC-7807 ProblemDetail contract.
        assert body["status"] == 422
        assert body["title"] == "Unprocessable Entity"
        assert "help_url" in body

    def test_openapi_documents_response_model(self) -> None:
        spec = app.openapi()
        path = spec["paths"]["/api/tips"]
        assert "get" in path
        schema = path["get"]["responses"]["200"]["content"]["application/json"][
            "schema"
        ]
        assert schema["type"] == "array"
        assert schema["items"]["$ref"].endswith("TipSchema")
