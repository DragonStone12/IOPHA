from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.dependencies import get_provider_repository
from app.main import app
from app.schemas import PhysicianSchema, ProviderRecord

# Substrings that must NEVER appear in a client-facing response.
LEAK_MARKERS = ("Traceback", "0x", "password", "secret", "Bearer ", "postgresql")


@pytest.fixture(autouse=True)
def isolate_database_layer() -> Generator[None, None, None]:
    """Swap the production repository for an in-memory double.

    Overrides ``get_provider_repository`` so no live datastore is touched, then
    clears every override in teardown to prevent state leaking across tests.
    """

    class MockProviderRepository:
        def find_by_id(self, provider_id: str) -> ProviderRecord | None:
            if provider_id == "missing":
                return None
            return ProviderRecord(
                id=provider_id,
                name="Dr. Emily Chen, MD",
                specialty="Cardiology",
                distance="1.8 miles",
                rating=4.9,
                reviewCount=120,
                nextAvailable="Today, 3:30 PM",
                imageUrl="https://cdn.example.com/emily.jpg",
                facility="Northside Medical Center",
                db_primary_key=42,
            )

    app.dependency_overrides[get_provider_repository] = lambda: MockProviderRepository()
    yield
    app.dependency_overrides.clear()


def test_fetch_physician_endpoint_success() -> None:
    with TestClient(app) as client:
        response = client.get("/api/providers/prov-123")
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Dr. Emily Chen, MD"
        assert body["reviewCount"] == 120
        assert body["facility"] == "Northside Medical Center"


def test_structural_identifier_never_leaks() -> None:
    with TestClient(app) as client:
        response = client.get("/api/providers/prov-123")
        body = response.json()
        # The internal persistence key is dropped by the mapping layer.
        assert "db_primary_key" not in body


def test_response_is_normalized_frontend_contract() -> None:
    with TestClient(app) as client:
        response = client.get("/api/providers/prov-123")
        body = response.json()
        assert set(body.keys()) == {
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


def test_echoes_supplied_request_id_header() -> None:
    valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
    with TestClient(app) as client:
        response = client.get(
            "/api/providers/prov-123",
            headers={"X-Request-ID": valid_uuid},
        )
        assert response.headers["X-Request-ID"] == valid_uuid


def test_missing_provider_returns_rfc7807_problem() -> None:
    with TestClient(app) as client:
        response = client.get("/api/providers/missing")
        assert response.status_code == 404
        body = response.json()
        assert body["title"] == "Provider Record Absent"
        assert body["status"] == 404
        assert "missing" in body["detail"]
        assert body["instance"] == "/api/providers/missing"
        assert body["help_url"].endswith("#provider-not-found-error")
        assert body["help_url"].startswith(
            "https://github.com/DragonStone12/IOPHA/blob/main/docs/RUNBOOKS.md#"
        )


def test_missing_provider_payload_contains_no_secrets() -> None:
    with TestClient(app) as client:
        response = client.get("/api/providers/missing")
        for marker in LEAK_MARKERS:
            assert marker not in response.text


# ---------------------------------------------------------------------------
# Service + schema unit tests (no HTTP / no datastore)
# ---------------------------------------------------------------------------


def test_map_provider_to_physician_drops_structural_id() -> None:
    from app.schemas import map_provider_to_physician

    record = ProviderRecord(
        id="prov-1",
        name="Dr. Jane Doe, MD",
        specialty="Dermatology",
        distance="2.1 miles",
        rating=4.7,
        reviewCount=88,
        nextAvailable="Tomorrow, 9:00 AM",
        db_primary_key=999,
    )
    physician = map_provider_to_physician(record)
    assert isinstance(physician, PhysicianSchema)
    assert physician.id == "prov-1"
    assert physician.model_dump().get("db_primary_key") is None


def test_physician_schema_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        PhysicianSchema(
            id="prov-1",
            name="Dr. Jane Doe, MD",
            specialty="Dermatology",
            distance="2.1 miles",
            rating=4.7,
            reviewCount=88,
            nextAvailable="Tomorrow, 9:00 AM",
            ssn="123-45-6789",  # type: ignore[call-arg]
        )


def test_provider_service_raises_when_absent() -> None:
    from app.exceptions import ProviderNotFoundException
    from app.repositories.provider_repository import InMemoryProviderRepository
    from app.services.provider_service import ProviderService

    service = ProviderService(InMemoryProviderRepository())
    with pytest.raises(ProviderNotFoundException) as exc_info:
        service.get_physician("ghost")
    assert exc_info.value.provider_id == "ghost"
    assert exc_info.value.status_code == 404
    assert exc_info.value.link == "provider-not-found-error"
