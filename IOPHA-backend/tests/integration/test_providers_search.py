import uuid
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_search_orchestrator
from app.main import app

LEAK_MARKERS = (
    "Traceback",
    "Exception(",
    "0x",
    "password",
    "secret",
    "Bearer ",
    "postgresql",
)


class MockSearchOrchestrator:
    """Fault-injectable search double for integration tests."""

    def __init__(self, timeout_query: str = "timeout-trigger") -> None:
        self._timeout_query = timeout_query

    def execute_query(self, query_string: str) -> dict:
        if query_string == self._timeout_query:
            raise SearchTimeoutError()
        return {
            "summaryText": "Found 1 doctor near you.",
            "providers": [
                {
                    "id": "doc-77",
                    "name": "Dr. Sam",
                    "specialty": "General",
                    "distance": "1.2 miles",
                    "rating": 5.0,
                    "reviewCount": 10,
                    "nextAvailable": "Tomorrow",
                    "imageUrl": "/static/img.png",
                }
            ],
            "followUpActions": [
                {
                    "label": "Book Now",
                    "actionType": "BOOK_PROVIDER",
                    "providerId": "doc-77",
                }
            ],
        }


class SearchTimeoutError(Exception):
    """Domain exception raised when the search aggregator times out."""


@pytest.fixture(autouse=True)
def bind_search_mock() -> Generator[None, None, None]:
    app.dependency_overrides[get_search_orchestrator] = lambda: MockSearchOrchestrator()
    yield
    app.dependency_overrides.pop(get_search_orchestrator, None)


class TestProviderSearchHappyPath:
    def test_search_returns_200(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/providers/search",
                json={"queryText": "Cardiologist"},
            )
        assert response.status_code == 200
        body = response.json()
        assert body["summaryText"] == "Found 1 doctor near you."
        assert len(body["providers"]) == 1
        assert body["providers"][0]["id"] == "doc-77"
        assert len(body["followUpActions"]) == 1
        assert body["followUpActions"][0]["actionType"] == "BOOK_PROVIDER"

    def test_response_matches_contract_schema(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/providers/search",
                json={"queryText": "Dermatologist"},
            )
        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {
            "summaryText",
            "providers",
            "followUpActions",
        }
        assert set(body["providers"][0].keys()) == {
            "id",
            "name",
            "specialty",
            "distance",
            "rating",
            "reviewCount",
            "nextAvailable",
            "imageUrl",
            "facility",
        }
        assert set(body["followUpActions"][0].keys()) == {
            "label",
            "actionType",
            "providerId",
        }


class TestProviderSearchValidation:
    def test_missing_query_text_returns_422(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/providers/search",
                json={},
            )
        assert response.status_code == 422


class TestProviderSearchContextPropagation:
    def test_request_id_generated_when_header_absent(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/providers/search",
                json={"queryText": "Cardiologist"},
            )
        assert response.status_code == 200
        echoed = response.headers.get("X-Request-ID")
        assert echoed is not None
        uuid.UUID(echoed)

    def test_request_id_echoed_on_success(self) -> None:
        request_id = "123e4567-e89b-12d3-a456-426614174000"
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/providers/search",
                json={"queryText": "Cardiologist"},
                headers={"X-Request-ID": request_id},
            )
        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == request_id


class TestProviderSearchLeakPrevention:
    def test_response_contains_no_leaked_data(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/providers/search",
                json={"queryText": "Cardiologist"},
            )
        for marker in LEAK_MARKERS:
            assert marker not in response.text


class TestProviderSearchDependencyIsolation:
    def test_overrides_cleared_between_tests(self) -> None:
        app.dependency_overrides[get_search_orchestrator] = lambda: (
            MockSearchOrchestrator()
        )
        assert get_search_orchestrator in app.dependency_overrides
        app.dependency_overrides.pop(get_search_orchestrator, None)
        assert get_search_orchestrator not in app.dependency_overrides
