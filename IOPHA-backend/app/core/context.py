import asyncio
import functools
import uuid
from collections.abc import Awaitable, Coroutine
from contextvars import ContextVar
from typing import Any, Callable, ParamSpec, TypeVar, cast

# Request correlation identifier threaded through every downstream operation
# (logging, repositories, services, background tasks) without being passed
# explicitly through function signatures. FastAPI/Starlette run the endpoint
# inside a task that inherits this context, so the value propagates
# automatically. Defaults to ``"system"`` when no request is active (e.g.
# unit tests that build LogRecords directly without an active request).
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="system")

P = ParamSpec("P")
R = TypeVar("R")


def get_request_id() -> str:
    """Return the correlation id bound to the current execution context."""
    return request_id_ctx.get()


def generate_request_id() -> str:
    """Mint a new standard tracking UUID for an inbound request."""
    return str(uuid.uuid4())


def preserve_request_context(func: Callable[P, R]) -> Callable[P, R]:
    """Bind the *current* correlation id into *func* for deferred execution.

    FastAPI/Starlette background tasks run **after** the request-tracking
    middleware's ``finally`` block has already reset ``request_id_ctx`` back to
    ``"system"``. A background task scheduled during a request therefore loses
    the request's correlation id and its logs become untraceable.

    This decorator snapshots the correlation id at wrap time (i.e. while the
    request context is still active) and re-binds it around every invocation,
    resetting it afterwards so nothing leaks. It supports both synchronous and
    ``async`` callables, so it can wrap any background task before it is handed
    to ``BackgroundTasks.add_task`` / ``asyncio.create_task``.

    Usage::

        background_tasks.add_task(preserve_request_context(send_receipt), tip_id)
    """
    captured_id = request_id_ctx.get()

    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            token = request_id_ctx.set(captured_id)
            try:
                return await func(*args, **kwargs)
            finally:
                request_id_ctx.reset(token)

        return cast(Callable[P, R], async_wrapper)

    @functools.wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        token = request_id_ctx.set(captured_id)
        try:
            return func(*args, **kwargs)
        finally:
            request_id_ctx.reset(token)

    return sync_wrapper


def run_with_request_context(
    coro: Awaitable[R],
    request_id: str | None = None,
) -> Coroutine[Any, Any, R]:
    """Wrap *coro* so it executes bound to a specific correlation id.

    Convenience for ``asyncio.create_task`` style fire-and-forget work: the id
    defaults to the one bound in the current context (captured eagerly) so the
    spawned task traces under the same request even once the parent context has
    been reset.
    """
    captured_id = request_id if request_id is not None else request_id_ctx.get()

    async def _runner() -> R:
        token = request_id_ctx.set(captured_id)
        try:
            return await coro
        finally:
            request_id_ctx.reset(token)

    return _runner()


__all__ = [
    "generate_request_id",
    "get_request_id",
    "preserve_request_context",
    "request_id_ctx",
    "run_with_request_context",
]
