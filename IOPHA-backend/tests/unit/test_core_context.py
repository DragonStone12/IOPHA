import asyncio

import pytest

from app.core.context import (
    generate_request_id,
    request_id_ctx,
)


class TestRequestIdContext:
    def test_default_is_system(self) -> None:
        assert request_id_ctx.get() == "system"

    def test_set_and_reset_returns_to_default(self) -> None:
        token = request_id_ctx.set("req-1")
        try:
            assert request_id_ctx.get() == "req-1"
        finally:
            request_id_ctx.reset(token)
        assert request_id_ctx.get() == "system"

    def test_generate_request_id_is_uuid(self) -> None:
        import uuid

        uuid.UUID(generate_request_id())

    def test_context_does_not_leak_across_calls(self) -> None:
        # Each set/reset cycle must restore the prior value, so consecutive
        # operations on the same task never bleed state into one another.
        token_a = request_id_ctx.set("a")
        try:
            assert request_id_ctx.get() == "a"
        finally:
            request_id_ctx.reset(token_a)

        token_b = request_id_ctx.set("b")
        try:
            assert request_id_ctx.get() == "b"
        finally:
            request_id_ctx.reset(token_b)

        assert request_id_ctx.get() == "system"

    @pytest.mark.asyncio
    async def test_context_isolated_between_concurrent_tasks(self) -> None:
        # Concurrent coroutines must observe independent context values and
        # never see each other's ids, even when run on the same event loop.
        results: dict[str, str] = {}

        async def worker(tag: str, value: str) -> None:
            token = request_id_ctx.set(value)
            try:
                await asyncio.sleep(0)
                results[tag] = request_id_ctx.get()
            finally:
                request_id_ctx.reset(token)

        await asyncio.gather(
            worker("x", "x-id"),
            worker("y", "y-id"),
            worker("z", "z-id"),
        )

        assert results == {"x": "x-id", "y": "y-id", "z": "z-id"}
        # The surrounding context is untouched by the child tasks.
        assert request_id_ctx.get() == "system"
