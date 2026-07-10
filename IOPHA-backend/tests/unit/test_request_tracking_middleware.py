import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import Response

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


@pytest.mark.asyncio
async def test_middleware_resets_context_after_dispatch() -> None:
    # Drive the middleware in-process (same event loop/task) so the
    # set/reset performed in dispatch is observable here. TestClient runs the
    # app on an isolated worker thread whose context is invisible to the test,
    # so it cannot prove the reset actually happened.
    observed: dict[str, str] = {}

    async def call_next(request: Request) -> Response:  # noqa: ARG001
        observed["during"] = request_id_ctx.get()
        return Response("ok")

    middleware = RequestTrackingMiddleware(app=FastAPI())
    valid = "123e4567-e89b-12d3-a456-426614174000"
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/ping",
        "query_string": b"",
        "headers": [(b"x-request-id", valid.encode())],
    }
    response = await middleware.dispatch(Request(scope), call_next)

    assert observed["during"] == valid
    assert response.headers["X-Request-ID"] == valid
    # The token is reset in THIS context once dispatch returns.
    assert request_id_ctx.get() == "system"
