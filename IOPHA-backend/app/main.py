from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="IOPHA Backend API")

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
