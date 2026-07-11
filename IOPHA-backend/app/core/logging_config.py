import logging

from app.utils.logging import LOGGER_NAME, JsonTelemetryFormatter, configure_logging


# Spec-named formatter for the availability API. It inherits the active
# telemetry formatter (which already threads ``requestId`` from the request
# context and scrubs PHI from every string value) and guarantees the
# documented field set: timestamp, level, requestId, method, path, message
# (method/path arrive via the middleware's ``extra_context``).
class JSONLogFormatter(JsonTelemetryFormatter):
    """Structured JSON formatter emitting the availability-API log contract."""


def configure_structured_logging(level: int = logging.INFO) -> logging.Logger:
    """Build and return the application logger wired to :class:`JSONLogFormatter`."""
    return configure_logging(level=level, formatter=JSONLogFormatter())


__all__ = [
    "JSONLogFormatter",
    "configure_structured_logging",
    "LOGGER_NAME",
]
