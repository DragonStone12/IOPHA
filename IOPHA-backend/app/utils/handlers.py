import logging
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

from app.exceptions import (
    DOMAIN_EXCEPTIONS,
    GITHUB_RUNBOOK_BASE_URL,
    IOPHADomainError,
)
from app.schemas.problem.problem_detail import ProblemDetail

# Logger namespace matches app.main so structured JSON records flow through
# the same JsonTelemetryFormatter pipeline as the request middleware.
logger = logging.getLogger("iopha.backend")

INTERNAL_SERVER_ERROR_LINK = "internal-server-error"
VALIDATION_ERROR_LINK = "request-validation-error"
HTTP_ERROR_LINK = "http-error"


def _help_url(link: str) -> str:
    """Build a deep-link into the centralized GitHub runbook document."""
    return f"{GITHUB_RUNBOOK_BASE_URL}#{link}"


def _request_id(request: Request) -> str:
    """Read the correlation id, degrading gracefully when the header is absent."""
    return request.headers.get("X-Request-ID", "unknown")


def _sanitized_validation_errors(
    exc: RequestValidationError,
) -> list[dict[str, Any]]:
    """Return field-level validation errors with raw input values stripped.

    ``exc.errors()`` includes the offending ``input`` for each field, which can
    carry PHI; we drop it (and ``ctx``) so nothing sensitive reaches the
    client response or logs.
    """
    cleaned: list[dict[str, Any]] = []
    for err in exc.errors():
        cleaned.append(
            {
                "loc": list(err.get("loc", [])),
                "msg": err.get("msg", ""),
                "type": err.get("type", ""),
            }
        )
    return cleaned


def _problem_response(  # noqa: PLR0913
    *,
    request: Request,
    status_code: int,
    title: str,
    detail: str,
    link: str,
    errors: list[dict[str, Any]] | None = None,  # noqa: PLR0913
) -> JSONResponse:
    payload = ProblemDetail(
        type="about:blank",
        title=title,
        status=status_code,
        detail=detail,
        instance=request.url.path,
        help_url=_help_url(link),
        errors=errors,
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def _domain_payload(exc: IOPHADomainError, request: Request) -> dict[str, object]:
    return {
        "type": "about:blank",
        "title": exc.title,
        "status": exc.status_code,
        "detail": exc.safe_detail(),
        "instance": request.url.path,
        "help_url": _help_url(exc.link),
    }


async def _domain_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global handler for every known IOPHA domain exception.

    Emits a structured, non-sensitive log record and returns a diagnostic
    RFC-7807-style problem payload with a runbook deep-link.
    """
    domain = exc if isinstance(exc, IOPHADomainError) else IOPHADomainError()
    context: dict[str, object] = {
        "requestId": _request_id(request),
        "path": request.url.path,
        **domain.log_context(),
    }
    logger.log(
        domain.log_level,
        domain.log_event,
        extra={"extra_context": context},
    )
    return JSONResponse(
        status_code=domain.status_code,
        content=_domain_payload(domain, request),
    )


async def _validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Project FastAPI input-validation faults into the RFC-7807 problem shape."""
    logger.warning(
        "request.validation_error",
        extra={
            "extra_context": {
                "requestId": _request_id(request),
                "path": request.url.path,
                "errorCount": len(exc.errors()),
            }
        },
    )
    return _problem_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="Request Validation Error",
        detail="The request failed input validation. Inspect 'errors' "
        "for field-level details.",
        link=VALIDATION_ERROR_LINK,
        errors=_sanitized_validation_errors(exc),
    )


async def _http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Normalize Starlette HTTP exceptions (404/405/...) into the problem shape."""
    logger.info(
        "request.http_error",
        extra={
            "extra_context": {
                "requestId": _request_id(request),
                "path": request.url.path,
                "status": exc.status_code,
            }
        },
    )
    return _problem_response(
        request=request,
        status_code=exc.status_code,
        title="HTTP Error",
        detail=str(exc.detail) if exc.detail else "The server rejected the request.",
        link=HTTP_ERROR_LINK,
    )


async def _global_unexpected_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for any unhandled runtime fault.

    The raw exception and stack trace are captured server-side only
    (exc_info=True). Nothing from the exception object leaks into the client
    response body.
    """
    request_id = _request_id(request)
    logger.error(
        "request.unexpected_error",
        exc_info=True,
        extra={
            "extra_context": {
                "requestId": request_id,
                "path": request.url.path,
                "userAgent": request.headers.get("user-agent", "unknown"),
            }
        },
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "detail": "An unexpected server-side process interruption occurred.",
            "instance": request.url.path,
            "help_url": _help_url(INTERNAL_SERVER_ERROR_LINK),
        },
    )


class ProblemAPIRoute(APIRoute):
    """Route class that funnels ``RequestValidationError`` into ``ProblemDetail``.

    FastAPI normally documents validation faults with the default
    ``HTTPValidationError`` schema. By catching the error inside the route
    handler wrapper we both return the real RFC-7807 problem object at runtime
    and let the OpenAPI document reflect the true error contract.
    """

    def get_route_handler(  # type: ignore[override]
        self,
    ) -> Callable[[StarletteRequest], Awaitable[Response]]:
        original = super().get_route_handler()

        async def route_handler(request: StarletteRequest) -> Response:
            try:
                return await original(request)
            except RequestValidationError as exc:
                return _validation_error_handler(request, exc)  # type: ignore[return-value]

        return route_handler


def register_exception_handlers(app: FastAPI) -> None:
    """Register all domain handlers plus the global catch-all on ``app``."""
    for exc_class in DOMAIN_EXCEPTIONS:
        app.add_exception_handler(exc_class, _domain_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _global_unexpected_handler)
