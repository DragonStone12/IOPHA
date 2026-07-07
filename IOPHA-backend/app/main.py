import logging
import re

from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, field_serializer
from starlette.middleware.base import BaseHTTPMiddleware

# ---------------------------------------------------------------------------
# 1. Pydantic DTOs with PII field serialization
# ---------------------------------------------------------------------------


class PatientDTO(BaseModel):
    patient_id: int
    name: str
    email: str
    phone: str
    medical_record_number: str

    @field_serializer("email", "phone", "medical_record_number")
    def mask_pii(self, value: str) -> str:
        return "[REDACTED]"


class ChatMessageDTO(BaseModel):
    message_id: str
    user_id: int
    content: str
    timestamp: str


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
        self.patterns = [
            (
                re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
                "[EMAIL_REDACTED]",
            ),
            (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "[PHONE_REDACTED]"),
            (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_REDACTED]"),
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        # 1. Scrub the main log message string
        if isinstance(record.msg, str):
            for pattern, replacement in self.patterns:
                record.msg = pattern.sub(replacement, record.msg)

        # 2. Scrub string arguments (handle tuple immutability)
        if record.args:
            if isinstance(record.args, dict):
                for key, value in record.args.items():
                    if isinstance(value, str):
                        sanitized = value
                        for pattern, replacement in self.patterns:
                            sanitized = pattern.sub(replacement, sanitized)
                        record.args[key] = sanitized
            elif isinstance(record.args, tuple):
                sanitized_args = []
                for arg in record.args:
                    if isinstance(arg, str):
                        for pattern, replacement in self.patterns:
                            arg = pattern.sub(replacement, arg)
                    sanitized_args.append(arg)
                record.args = tuple(sanitized_args)

        # 3. Scrub the 'extra' dictionary (structured JSON logging context)
        if hasattr(record, "extra") and record.extra:
            for key, value in record.extra.items():
                if isinstance(value, str):
                    sanitized = value
                    for pattern, replacement in self.patterns:
                        sanitized = pattern.sub(replacement, sanitized)
                    record.extra[key] = sanitized

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

    async def dispatch(self, request: Request, call_next):
        # 1. Sanitize URL Path
        sanitized_path = re.sub(r"/patients/\d+", "/patients/:id", request.url.path)
        sanitized_path = re.sub(r"/providers/\d+", "/providers/:id", sanitized_path)

        # 2. Sanitize Query Parameters
        sensitive_keys = {"ssn", "email", "phone", "medical_record_number"}
        sanitized_query = {}
        for key, value in request.query_params.items():
            if key.lower() in sensitive_keys:
                sanitized_query[key] = "[REDACTED]"
            else:
                sanitized_query[key] = value

        # 3. Attach to request.state for downstream middleware
        request.state.sanitized_path = sanitized_path
        request.state.sanitized_query = sanitized_query

        response = await call_next(request)
        return response


# Register middleware BEFORE logging and metrics middleware
app.add_middleware(PIISanitizationMiddleware)

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
