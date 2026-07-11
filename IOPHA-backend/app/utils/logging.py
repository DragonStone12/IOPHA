import json
import logging
import time
from collections.abc import Awaitable
from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.phi_scrubber import PHIScrubber
from app.utils.context import request_id_ctx

_scrubber = PHIScrubber()


class JsonTelemetryFormatter(logging.Formatter):
    """
    Structured JSON formatter for CloudWatch / Elasticsearch ingestion.
    Emits strict root-level attributes required by the telemetry pipeline.

    Every line carries ``requestId``, sourced from the active request
    correlation context (``app.context.request_id_ctx``) so downstream
    operations (services, repositories, background tasks) are traceable
    without threading the id through function signatures. Only curated
    fields are emitted -- raw credentials, structural identifiers, and other
    ``record`` internals are never serialized to stdout.
    """

    ISO_8601_DATEFMT = "%Y-%m-%dT%H:%M:%S%:z"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("datefmt", self.ISO_8601_DATEFMT)
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        log_payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": _scrubber.scrub_message(record.getMessage()),
            "requestId": request_id_ctx.get(),
        }

        if hasattr(record, "extra_context"):
            # Scrub any human-readable string values; structured/non-string
            # values (dicts, ints) are passed through untouched.
            for key, value in record.extra_context.items():
                log_payload[key] = (
                    _scrubber.scrub_message(value) if isinstance(value, str) else value
                )

        if record.exc_info:
            log_payload["exc_info"] = _scrubber.scrub_message(
                self.formatException(record.exc_info)
            )

        if record.stack_info:
            log_payload["stack_info"] = _scrubber.scrub_message(
                self.formatStack(record.stack_info)
            )

        return json.dumps(log_payload, default=str)

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:  # noqa: N802
        datefmt = datefmt or self.ISO_8601_DATEFMT
        return datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(datefmt)


LOGGER_NAME = "iopha.backend"


def configure_logging(
    level: int = logging.INFO,
    formatter: logging.Formatter | None = None,
) -> logging.Logger:
    """Build and register the structured JSON logger used by the app.

    Attaches a stdout :class:`logging.StreamHandler` wrapped in
    :class:`JsonTelemetryFormatter` (or a caller-supplied formatter) and
    disables propagation so records are emitted once, in machine-readable
    JSON, for external log shippers.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(formatter or JsonTelemetryFormatter())
        logger.addHandler(handler)
    return logger


def get_logger() -> logging.Logger:
    """Return the application logger, configuring it on first use."""
    return configure_logging()


class CentralizedLoggingMiddleware(BaseHTTPMiddleware):
    """
    Asynchronous request/response logging middleware.
    Produces structured JSON log entries for every HTTP transaction.
    """

    def __init__(self, app: Any, logger: logging.Logger | None = None) -> None:
        super().__init__(app)
        self.logger = logger or get_logger()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start_time = time.time()

        raw_path = request.url.path
        query_params = dict(request.query_params)

        self.logger.info(
            "request.start",
            extra={
                "extra_context": {
                    "method": request.method,
                    "path": raw_path,
                    "userAgent": request.headers.get("user-agent", "unknown"),
                    "queryParams": query_params,
                }
            },
        )

        response = await call_next(request)

        duration_ms = int((time.time() - start_time) * 1000)
        raw_response_size = response.headers.get("content-length", "0")
        response_size = int(raw_response_size) if raw_response_size.isdigit() else 0

        self.logger.info(
            "request.complete",
            extra={
                "extra_context": {
                    "status": response.status_code,
                    "durationMs": duration_ms,
                    "responseSize": response_size,
                }
            },
        )

        return response
