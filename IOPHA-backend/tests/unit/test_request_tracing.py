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
    response = client.get("/ping", headers={"X-Request-ID": "client-abc"})
    assert response.headers["X-Request-ID"] == "client-abc"
    assert response.json()["requestId"] == "client-abc"


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
