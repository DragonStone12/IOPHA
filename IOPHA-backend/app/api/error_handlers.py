import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.exceptions.timeslot_exceptions import (
    InvalidTimeSlotFormatException,
    ProviderNotFoundException,
    TimeSlotUnavailableException,
)
from app.schemas.problem.problem_detail import ProblemDetail

GITHUB_RUNBOOK_BASE_URL = (
    "https://github.com/DragonStone12/IOPHA/blob/main/docs/RUNBOOKS.md"
)

logger = logging.getLogger("iopha.backend")


def _help_url(link: str) -> str:
    return f"{GITHUB_RUNBOOK_BASE_URL}#{link}"


def _request_id(request: Request) -> str:
    return request.headers.get("X-Request-ID", "unknown")


def format_problem_detail(  # noqa: PLR0913
    *,
    request: Request,
    status_code: int,
    title: str,
    detail: str,
    instance: str,
    help_url: str,
    request_id: str,
) -> JSONResponse:
    payload = ProblemDetail(
        title=title,
        status=status_code,
        detail=detail,
        instance=instance,
        help_url=help_url,
        type="about:blank",
        requestId=request_id,
        errors=None,
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


async def _timeslot_unavailable_handler(
    request: Request, exc: TimeSlotUnavailableException
) -> JSONResponse:
    context = {
        "requestId": _request_id(request),
        "path": request.url.path,
        **exc.log_context(),
    }
    logger.warning(
        "timeslot.unavailable",
        extra={"extra_context": context},
    )
    return format_problem_detail(
        request=request,
        status_code=status.HTTP_409_CONFLICT,
        title=exc.title,
        detail=exc.safe_detail(),
        instance=request.url.path,
        help_url=_help_url(exc.link),
        request_id=_request_id(request),
    )


async def _provider_not_found_handler(
    request: Request, exc: ProviderNotFoundException
) -> JSONResponse:
    context = {
        "requestId": _request_id(request),
        "path": request.url.path,
        **exc.log_context(),
    }
    logger.warning(
        "directory.provider_not_found",
        extra={"extra_context": context},
    )
    return format_problem_detail(
        request=request,
        status_code=status.HTTP_404_NOT_FOUND,
        title=exc.title,
        detail=exc.safe_detail(),
        instance=request.url.path,
        help_url=_help_url(exc.link),
        request_id=_request_id(request),
    )


async def _invalid_format_handler(
    request: Request, exc: InvalidTimeSlotFormatException
) -> JSONResponse:
    context = {
        "requestId": _request_id(request),
        "path": request.url.path,
        **exc.log_context(),
    }
    logger.warning(
        "timeslot.invalid_format",
        extra={"extra_context": context},
    )
    return format_problem_detail(
        request=request,
        status_code=status.HTTP_400_BAD_REQUEST,
        title=exc.title,
        detail=exc.safe_detail(),
        instance=request.url.path,
        help_url=_help_url(exc.link),
        request_id=_request_id(request),
    )


def register_timeslot_error_handlers(app: FastAPI) -> None:
    """Register explicit exception handlers for the Time Slot Availability API.

    Handlers are registered using ``@app.exception_handler()`` so they
    intercept the specific domain exceptions before the global catch-all.
    """
    app.add_exception_handler(
        TimeSlotUnavailableException,
        _timeslot_unavailable_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        ProviderNotFoundException,
        _provider_not_found_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        InvalidTimeSlotFormatException,
        _invalid_format_handler,  # type: ignore[arg-type]
    )
