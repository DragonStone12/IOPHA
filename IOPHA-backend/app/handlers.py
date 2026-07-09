import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.exceptions import (
    DOMAIN_EXCEPTIONS,
    GITHUB_RUNBOOK_BASE_URL,
    IOPHADomainError,
)

# Logger namespace matches app.main so structured JSON records flow through
# the same JsonTelemetryFormatter pipeline as the request middleware.
logger = logging.getLogger("iopha.backend")

INTERNAL_SERVER_ERROR_LINK = "internal-server-error"


def _help_url(link: str) -> str:
    """Build a deep-link into the centralized GitHub runbook document."""
    return f"{GITHUB_RUNBOOK_BASE_URL}#{link}"


def _request_id(request: Request) -> str:
    """Read the correlation id, degrading gracefully when the header is absent."""
    return request.headers.get("X-Request-ID", "unknown")


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


def register_exception_handlers(app: FastAPI) -> None:
    """Register all domain handlers plus the global catch-all on ``app``."""
    for exc_class in DOMAIN_EXCEPTIONS:
        app.add_exception_handler(exc_class, _domain_handler)
    app.add_exception_handler(Exception, _global_unexpected_handler)
