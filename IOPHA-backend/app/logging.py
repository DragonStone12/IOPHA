import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Minimum number of trailing digits preserved when masking a user identifier.
MIN_MASKED_DIGITS = 3


class JsonTelemetryFormatter(logging.Formatter):
    """
    Structured JSON formatter for CloudWatch / Elasticsearch ingestion.
    Emits strict root-level attributes required by the telemetry pipeline.

    The `timestamp` field is emitted in strict ISO 8601 format via an explicit
    `datefmt`, satisfying the contract documented in TECHNICAL_DESIGN.md.
    """

    ISO_8601_DATEFMT = "%Y-%m-%dT%H:%M:%S%z"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("datefmt", self.ISO_8601_DATEFMT)
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        log_payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra_context"):
            log_payload.update(record.extra_context)

        if record.exc_info:
            log_payload["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info:
            log_payload["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(log_payload, default=str)

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:  # noqa: N802
        datefmt = datefmt or self.ISO_8601_DATEFMT
        return datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(datefmt)


class PathSanitizer:
    """
    Normalizes dynamic URL paths and masks sensitive identifiers
    to prevent cardinality explosion in metrics and PHI leakage in logs.
    """

    PATH_PATTERNS = [
        (re.compile(r"/patients/\d+"), "/patients/:id"),
        (re.compile(r"/providers/\d+"), "/providers/:id"),
        (re.compile(r"/sessions/\d+"), "/sessions/:id"),
        (re.compile(r"/users/\d+"), "/users/:id"),
    ]

    SENSITIVE_QUERY_KEYS = {
        "ssn",
        "email",
        "phone",
        "medical_record_number",
        "mrn",
        "dob",
        "date_of_birth",
    }

    @classmethod
    def sanitize_path(cls, raw_path: str) -> str:
        sanitized = raw_path
        for pattern, replacement in cls.PATH_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized

    @classmethod
    def sanitize_query(cls, query_params: dict[str, str]) -> dict[str, str]:
        sanitized: dict[str, str] = {}
        for key, value in query_params.items():
            if key.lower() in cls.SENSITIVE_QUERY_KEYS:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized

    @classmethod
    def mask_user_id(cls, user_id: str) -> str:
        match = re.match(r"^(.*?)(\d+)$", user_id)
        if match and len(match.group(2)) > MIN_MASKED_DIGITS:
            return f"{match.group(1)}***{match.group(2)[-MIN_MASKED_DIGITS:]}"
        return "[REDACTED_USER]"


class CentralizedLoggingMiddleware(BaseHTTPMiddleware):
    """
    Asynchronous request/response logging middleware.
    Produces structured JSON log entries for every HTTP transaction.
    """

    def __init__(self, app: Any, logger: logging.Logger | None = None) -> None:
        super().__init__(app)
        self.logger = logger or logging.getLogger("iopha.backend")

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", "unknown")

        raw_path = request.url.path
        sanitized_path = PathSanitizer.sanitize_path(raw_path)

        query_params = PathSanitizer.sanitize_query(dict(request.query_params))

        masked_user = (
            PathSanitizer.mask_user_id(request_id)
            if request_id != "unknown"
            else request_id
        )

        self.logger.info(
            "request.start",
            extra={
                "extra_context": {
                    "requestId": masked_user,
                    "method": request.method,
                    "path": sanitized_path,
                    "userAgent": request.headers.get("user-agent", "unknown"),
                    "queryParams": query_params,
                }
            },
        )

        response = await call_next(request)

        duration_ms = int((time.time() - start_time) * 1000)
        response_size = response.headers.get("content-length", "0")
        if isinstance(response_size, str) and response_size.isdigit():
            response_size = int(response_size)
        else:
            response_size = 0

        self.logger.info(
            "request.complete",
            extra={
                "extra_context": {
                    "requestId": masked_user,
                    "status": response.status_code,
                    "durationMs": duration_ms,
                    "responseSize": response_size,
                }
            },
        )

        return response
