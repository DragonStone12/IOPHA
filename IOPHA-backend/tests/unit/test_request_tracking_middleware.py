import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.context import get_request_id, request_id_ctx
from app.middleware.tracking import RequestTrackingMiddleware


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestTrackingMiddleware)

    @app.get("/ping")
    def ping() -> dict[str, str]:
        # Reflects the context-bound correlation id set by the middleware.
        return {"requestId": get_request_id()}

    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(_make_app())


def test_generates_request_id_when_header_absent(client: TestClient) -> None:
    response = client.get("/ping")
    assert response.status_code == 200
    echoed = response.headers.get("X-Request-ID")
    assert echoed is not None
    assert response.json()["requestId"] == echoed
    uuid.UUID(echoed)


def test_propagates_supplied_request_id(client: TestClient) -> None:
    valid = "123e4567-e89b-12d3-a456-426614174000"
    response = client.get("/ping", headers={"X-Request-ID": valid})
    assert response.headers["X-Request-ID"] == valid
    assert response.json()["requestId"] == valid


def test_rejects_invalid_uuid_and_generates_new(client: TestClient) -> None:
    response = client.get("/ping", headers={"X-Request-ID": "client-abc"})
    echoed = response.headers["X-Request-ID"]
    assert echoed is not None
    assert echoed != "client-abc"
    uuid.UUID(echoed)


def test_context_is_reset_after_request(client: TestClient) -> None:
    client.get("/ping", headers={"X-Request-ID": "temp-1"})
    # After the request completes the context must fall back to the default.
    assert request_id_ctx.get() == "system"
