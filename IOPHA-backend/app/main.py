import logging

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.handlers import register_exception_handlers
from app.logging import CentralizedLoggingMiddleware, JsonTelemetryFormatter

app = FastAPI(title="IOPHA Backend API")

register_exception_handlers(app)


log_handler = logging.StreamHandler()
log_handler.setFormatter(JsonTelemetryFormatter())
logger = logging.getLogger("iopha.backend")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
logger.propagate = False


app.add_middleware(CentralizedLoggingMiddleware, logger=logger)


instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_group_untemplated=True,
    should_respect_env_var=False,
    excluded_handlers=["/metrics"],
)

instrumentator.instrument(app).expose(
    app,
    endpoint="/metrics",
    should_gzip=True,
    include_in_schema=False,
    tags=["iopha_monitoring"],
)
