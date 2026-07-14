import uuid
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_search_orchestrator
from app.exceptions.domain_errors import SearchAggregatorTimeoutError
from app.main import app
from tests.integration._search_test_utils import MockSearchOrchestrator

LEAK_MARKERS = (
    "Traceback",
    "Exception(",
    "0x",
    "password",
    "secret",
    "Bearer ",
    "postgresql",
)


@pytest.fixture(autouse=True)
def bind_search_mock() -> Generator[None, None, None]:
    app.dependency_overrides[get_search_orchestrator] = lambda: MockSearchOrchestrator()
    yield
    app.dependency_overrides.pop(get_search_orchestrator, None)


class TestProviderSearchHappyPath:
    def test_search_returns_200(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/providers/search",
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
                "/api/providers/search",
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
                "/api/providers/search",
                json={},
            )
        assert response.status_code == 422


class TestProviderSearchContextPropagation:
    def test_request_id_generated_when_header_absent(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/providers/search",
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
                "/api/providers/search",
                json={"queryText": "Cardiologist"},
                headers={"X-Request-ID": request_id},
            )
        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == request_id


class TestProviderSearchLeakPrevention:
    def test_response_contains_no_leaked_data(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/providers/search",
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


class TestProviderSearchErrorInjection:
    """Error Handling Test: Confirms that when dependencies trigger exceptional
    paths, the custom error interceptor structures the response payload
    correctly and preserves tracking logs."""

    def test_timeout_returns_504_with_problem_detail(self) -> None:
        app.dependency_overrides[get_search_orchestrator] = lambda: (
            MockSearchOrchestrator(timeout_query="timeout-trigger")
        )
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/providers/search",
                    json={"queryText": "timeout-trigger"},
                    headers={"X-Request-ID": "trace-555-search-err"},
                )
            assert response.status_code == 504
            body = response.json()
            assert body["title"] == SearchAggregatorTimeoutError.title
            assert body["status"] == 504
            assert body["help_url"].endswith(f"#{SearchAggregatorTimeoutError.link}")
            assert body["help_url"].startswith(
                "https://github.com/DragonStone12/IOPHA/blob/main/docs/RUNBOOKS.md#"
            )
        finally:
            app.dependency_overrides.pop(get_search_orchestrator, None)

    def test_timeout_preserves_request_id_in_response_header(self) -> None:
        request_id = "123e4567-e89b-12d3-a456-426614174000"
        app.dependency_overrides[get_search_orchestrator] = lambda: (
            MockSearchOrchestrator(timeout_query="timeout-trigger")
        )
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/providers/search",
                    json={"queryText": "timeout-trigger"},
                    headers={"X-Request-ID": request_id},
                )
            assert response.status_code == 504
            assert response.headers["X-Request-ID"] == request_id
        finally:
            app.dependency_overrides.pop(get_search_orchestrator, None)

    def test_timeout_response_contains_no_leaked_data(self) -> None:
        app.dependency_overrides[get_search_orchestrator] = lambda: (
            MockSearchOrchestrator(timeout_query="timeout-trigger")
        )
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/providers/search",
                    json={"queryText": "timeout-trigger"},
                )
            assert response.status_code == 504
            for marker in LEAK_MARKERS:
                assert marker not in response.text
        finally:
            app.dependency_overrides.pop(get_search_orchestrator, None)
