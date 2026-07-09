from collections.abc import Awaitable
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.utils.context import generate_request_id, request_id_ctx


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """ASGI interceptor that guarantees every request carries a correlation id.

    Reads ``X-Request-ID`` from the inbound headers; if absent, mints a new
    UUID. The value is bound to :data:`app.context.request_id_ctx` for the
    lifetime of the request so downstream logging, services, repositories,
    and background tasks can attach the same trace without parameter
    threading. The resolved id is echoed back on the response header for
    client-side correlation.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        req_id = request.headers.get("X-Request-ID") or generate_request_id()
        token = request_id_ctx.set(req_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx.reset(token)
