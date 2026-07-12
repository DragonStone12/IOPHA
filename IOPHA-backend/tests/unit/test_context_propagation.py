import asyncio

import pytest
from fastapi import BackgroundTasks, FastAPI
from fastapi.testclient import TestClient

from app.core.context import (
    get_request_id,
    preserve_request_context,
    request_id_ctx,
    run_with_request_context,
)
from app.middleware.tracking import RequestTrackingMiddleware


class TestPreserveRequestContextSync:
    def test_wrapper_rebinds_captured_id_after_reset(self) -> None:
        # Simulate a background task: the wrapper is created while the request
        # context is active, then invoked later once the middleware has reset
        # the context back to the default.
        token = request_id_ctx.set("req-during-request")
        wrapped = preserve_request_context(lambda: get_request_id())
        request_id_ctx.reset(token)

        # Context is back to the default now (as it would be post-middleware).
        assert request_id_ctx.get() == "system"
        # ...but the deferred task still runs under the captured id.
        assert wrapped() == "req-during-request"
        # And the wrapper cleans up after itself (no leak).
        assert request_id_ctx.get() == "system"

    def test_wrapper_forwards_args_and_return_value(self) -> None:
        token = request_id_ctx.set("req-7")
        wrapped = preserve_request_context(lambda a, b: (a + b, get_request_id()))
        request_id_ctx.reset(token)

        assert wrapped(2, 3) == (5, "req-7")

    def test_plain_callable_loses_context_after_reset(self) -> None:
        # Documents the bottleneck this helper solves: an *unwrapped* callable
        # invoked after the reset sees only the default id.
        token = request_id_ctx.set("req-lost")
        request_id_ctx.reset(token)
        assert get_request_id() == "system"


class TestPreserveRequestContextAsync:
    @pytest.mark.asyncio
    async def test_async_wrapper_rebinds_captured_id(self) -> None:
        async def read_id() -> str:
            await asyncio.sleep(0)
            return get_request_id()

        token = request_id_ctx.set("async-req")
        wrapped = preserve_request_context(read_id)
        request_id_ctx.reset(token)

        assert await wrapped() == "async-req"
        assert request_id_ctx.get() == "system"

    @pytest.mark.asyncio
    async def test_concurrent_wrapped_tasks_do_not_bleed(self) -> None:
        async def read_id() -> str:
            await asyncio.sleep(0)
            return get_request_id()

        wrappers = []
        for value in ("id-a", "id-b", "id-c"):
            token = request_id_ctx.set(value)
            wrappers.append(preserve_request_context(read_id))
            request_id_ctx.reset(token)

        results = await asyncio.gather(*(w() for w in wrappers))
        assert results == ["id-a", "id-b", "id-c"]
        assert request_id_ctx.get() == "system"


class TestRunWithRequestContext:
    @pytest.mark.asyncio
    async def test_spawned_task_inherits_captured_id(self) -> None:
        async def read_id() -> str:
            await asyncio.sleep(0)
            return get_request_id()

        token = request_id_ctx.set("spawn-req")
        task = asyncio.create_task(run_with_request_context(read_id()))
        # Reset immediately, as the parent request context would be.
        request_id_ctx.reset(token)

        assert await task == "spawn-req"

    @pytest.mark.asyncio
    async def test_explicit_request_id_overrides_context(self) -> None:
        async def read_id() -> str:
            return get_request_id()

        result = await run_with_request_context(read_id(), request_id="forced")
        assert result == "forced"


class TestBackgroundTaskIntegration:
    def test_background_task_traces_under_request_id(self) -> None:
        captured: dict[str, str] = {}

        app = FastAPI()
        app.add_middleware(RequestTrackingMiddleware)

        def record_trace() -> None:
            captured["requestId"] = get_request_id()

        @app.get("/schedule")
        def schedule(background_tasks: BackgroundTasks) -> dict[str, str]:
            # Wrap so the deferred task keeps the request's correlation id even
            # though the middleware resets the context once dispatch returns.
            background_tasks.add_task(preserve_request_context(record_trace))
            return {"requestId": get_request_id()}

        valid = "123e4567-e89b-12d3-a456-426614174000"
        with TestClient(app) as client:
            response = client.get("/schedule", headers={"X-Request-ID": valid})

        assert response.status_code == 200
        assert response.json()["requestId"] == valid
        # The background task ran under the same correlation id.
        assert captured["requestId"] == valid
