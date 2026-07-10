import uuid
from collections.abc import Awaitable
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.utils.context import generate_request_id, request_id_ctx


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """ASGI interceptor that guarantees every request carries a correlation id.

    Reads ``X-Request-ID`` from the inbound headers; if absent or malformed,
    mints a new UUID. Only syntactically valid UUIDs are trusted from the
    client to prevent log injection / trace spoofing. The resolved id is
    bound to :data:`app.context.request_id_ctx` for the lifetime of the
    request so downstream logging, services, repositories, and background
    tasks can attach the same trace without parameter threading. The
    resolved id is echoed back on the response header for client-side
    correlation.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        raw_req_id = request.headers.get("X-Request-ID")
        if raw_req_id and _is_valid_uuid(raw_req_id):
            req_id = raw_req_id
        else:
            req_id = generate_request_id()
        token = request_id_ctx.set(req_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx.reset(token)


def _is_valid_uuid(value: str | None) -> bool:
    """Return ``True`` only if *value* is a syntactically valid UUID."""
    if not value:
        return False
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False
