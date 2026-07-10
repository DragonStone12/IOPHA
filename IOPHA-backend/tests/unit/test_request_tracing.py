import logging
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware import RequestTracingMiddleware
from app.utils.context import get_request_id, request_id_ctx
from app.utils.logging import JsonTelemetryFormatter


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestTracingMiddleware)

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
    # The generated id is a well-formed UUID.
    uuid.UUID(echoed)


def test_propagates_supplied_request_id(client: TestClient) -> None:
    valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
    response = client.get("/ping", headers={"X-Request-ID": valid_uuid})
    assert response.headers["X-Request-ID"] == valid_uuid
    assert response.json()["requestId"] == valid_uuid


def test_rejects_invalid_uuid_and_generates_new(client: TestClient) -> None:
    response = client.get("/ping", headers={"X-Request-ID": "client-abc"})
    echoed = response.headers["X-Request-ID"]
    assert echoed is not None
    assert echoed != "client-abc"
    # The generated id is a well-formed UUID.
    uuid.UUID(echoed)


def test_rejects_empty_string_and_generates_new(client: TestClient) -> None:
    response = client.get("/ping", headers={"X-Request-ID": ""})
    echoed = response.headers["X-Request-ID"]
    assert echoed is not None
    uuid.UUID(echoed)


def test_rejects_script_injection_and_generates_new(client: TestClient) -> None:
    response = client.get(
        "/ping",
        headers={"X-Request-ID": "<script>alert(1)</script>"},
    )
    echoed = response.headers["X-Request-ID"]
    assert echoed is not None
    uuid.UUID(echoed)


def test_rejects_oversized_header_and_generates_new(client: TestClient) -> None:
    response = client.get("/ping", headers={"X-Request-ID": "a" * 1025})
    echoed = response.headers["X-Request-ID"]
    assert echoed is not None
    uuid.UUID(echoed)


def test_context_is_reset_after_request(client: TestClient) -> None:
    client.get("/ping", headers={"X-Request-ID": "temp-1"})
    # After the request completes the context must fall back to the default.
    assert request_id_ctx.get() == "system"


def test_formatter_reads_context_request_id() -> None:
    token = request_id_ctx.set("trace-99")
    try:
        record = logging.LogRecord(
            name="iopha.backend",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="request.start",
            args=(),
            exc_info=None,
        )
        payload = JsonTelemetryFormatter().format(record)
        assert '"requestId": "trace-99"' in payload
    finally:
        request_id_ctx.reset(token)
