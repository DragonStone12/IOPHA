from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.controllers.providers import router as providers_router
from app.middleware import RequestTracingMiddleware
from app.utils.handlers import register_exception_handlers
from app.utils.logging import CentralizedLoggingMiddleware, configure_logging

app = FastAPI(title="IOPHA Backend API")

register_exception_handlers(app)

logger = configure_logging()
app.add_middleware(CentralizedLoggingMiddleware, logger=logger)
app.add_middleware(RequestTracingMiddleware)
app.include_router(providers_router)

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
