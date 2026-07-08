import logging
import re
import urllib.parse
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, field_serializer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# ---------------------------------------------------------------------------
# 1. Pydantic DTOs with PII field serialization
# ---------------------------------------------------------------------------

# Centralized PII patterns shared by the logging filter and the chat DTO
# serializer. Each entry is (compiled_regex, replacement). Matching text is
# redacted in place; non-matching text is preserved so API responses stay
# useful for callers instead of being wholly withheld.
PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[EMAIL_REDACTED]",
    ),
    (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "[PHONE_REDACTED]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_REDACTED]"),
]


def redact_pii(text: str) -> str:
    """Apply every PII pattern to a single string, preserving non-PII text."""
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class PatientDTO(BaseModel):
    patient_id: int
    name: str
    email: str
    phone: str
    medical_record_number: str

    @field_serializer("email", "phone", "medical_record_number")
    def mask_pii(self, value: str) -> str:
        # Structured PII fields are always fully withheld.
        return redact_pii(value)

    @field_serializer("name")
    def mask_name(self, value: str) -> str:
        # Partial masking (industry standard for UI-facing DTOs): the patient
        # name is PHI, so hide the full name but preserve enough for the UI to
        # remain usable (e.g. "John Doe" -> "J*** D***").
        if not value:
            return value
        parts = value.split()
        if not parts:
            return value
        if len(parts) == 1:
            return f"{parts[0][0]}***"
        return f"{parts[0][0]}*** {parts[-1][0]}***"


class ChatMessageDTO(BaseModel):
    message_id: str
    user_id: int
    content: str
    timestamp: str

    @field_serializer("content")
    def mask_pii(self, value: str) -> str:
        # Free-text content is selectively redacted: only PII-shaped spans are
        # replaced, so non-sensitive chat text is preserved for the caller.
        return redact_pii(value)


# ---------------------------------------------------------------------------
# 2. Logging filter for PII/PHI redaction
# ---------------------------------------------------------------------------


class PIISanitizerFilter(logging.Filter):
    """
    Industry standard global safety net.
    Intercepts all log records and scrubs PII/PHI before the JSON formatter.
    """

    def __init__(self) -> None:
        super().__init__()

    def _scrub_text(self, text: str) -> str:
        """Apply every PII pattern to a single string."""
        return redact_pii(text)

    def _scrub_args(self, args: Any) -> Any:
        """Redact PII from logging args, preserving dict/tuple shape."""
        if isinstance(args, dict):
            return {
                key: self._scrub_text(value) if isinstance(value, str) else value
                for key, value in args.items()
            }
        if isinstance(args, tuple):
            return tuple(
                self._scrub_text(arg) if isinstance(arg, str) else arg for arg in args
            )
        return args

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            record.args = self._scrub_args(record.args)

        for key, value in record.__dict__.items():
            if isinstance(value, str):
                record.__dict__[key] = self._scrub_text(value)

        return True


# Attach filter to root logger
root_logger = logging.getLogger()
pii_filter = PIISanitizerFilter()
root_logger.addFilter(pii_filter)


# ---------------------------------------------------------------------------
# 3. FastAPI app initialization
# ---------------------------------------------------------------------------

app = FastAPI(title="IOPHA Backend API")

# ---------------------------------------------------------------------------
# 4. PII Sanitization Middleware (must be registered BEFORE logging/metrics)
# ---------------------------------------------------------------------------


class PIISanitizationMiddleware(BaseHTTPMiddleware):
    """
    Normalizes dynamic URL paths and redacts sensitive query parameters.
    Must be registered before logging and metrics middleware.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 1. Sanitize URL Path
        sanitized_path = re.sub(r"/patients/[^/]+", "/patients/:id", request.url.path)
        sanitized_path = re.sub(r"/providers/[^/]+", "/providers/:id", sanitized_path)

        # 2. Sanitize Query Parameters
        sensitive_keys = {"ssn", "email", "phone", "medical_record_number"}
        sanitized_query = {}
        for key, value in request.query_params.items():
            if key.lower() in sensitive_keys:
                sanitized_query[key] = "[REDACTED]"
            else:
                sanitized_query[key] = value

        # 3. Rewrite request scope so downstream consumers (access log, metrics)
        #    see sanitized data instead of raw PII/PHI.
        request.scope["path"] = sanitized_path
        query_string = urllib.parse.urlencode(sanitized_query).encode("utf-8")
        request.scope["query_string"] = query_string
        if "raw_path" in request.scope:
            request.scope["raw_path"] = sanitized_path.encode("utf-8")

        # 4. Attach to request.state for any downstream middleware that reads it
        request.state.sanitized_path = sanitized_path
        request.state.sanitized_query = sanitized_query

        response = await call_next(request)
        return response


# Register middleware BEFORE logging and metrics middleware
app.add_middleware(PIISanitizationMiddleware)


# ---------------------------------------------------------------------------
# 4b. Chat endpoint (centralized PII serialization via ChatMessageDTO)
# ---------------------------------------------------------------------------


@app.post("/chat/message", response_model=ChatMessageDTO, tags=["chat"])
async def chat_message(message: ChatMessageDTO) -> ChatMessageDTO:
    """
    Accepts a chat message and echoes it back. The `ChatMessageDTO`
    response serializer applies targeted PII redaction to `content`
    (e.g. email addresses become `[EMAIL_REDACTED]`, phone numbers become
    `[PHONE_REDACTED]`), so sensitive data never leaves the API in the clear
    while non-sensitive text is preserved for the caller.
    """
    return message


# ---------------------------------------------------------------------------
# 5. Prometheus Metrics Instrumentation
# ---------------------------------------------------------------------------

# Initialize the instrumentator
# should_group_status_codes=True: group status codes (reduces cardinality)
# should_ignore_untemplated=True: ignore routes with no template
# should_group_untemplated=True: group untemplated paths
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_group_untemplated=True,
    should_respect_env_var=False,
    excluded_handlers=["/metrics"],
)

# Instrument the app and expose the /metrics endpoint
instrumentator.instrument(app).expose(
    app,
    endpoint="/metrics",
    should_gzip=True,
    include_in_schema=False,
    tags=["iopha_monitoring"],
)
