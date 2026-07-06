from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="IOPHA Backend API")

# Initialize the instrumentator
# should_group_status_codes=True groups similar status codes to reduce metric cardinality
# should_ignore_untemplated=True ignores metrics for requests that don't match any route
# should_group_untemplated=True groups untemplated paths to prevent cardinality explosion
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

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/directory")
def directory():
    return {"physicians": []}

@app.post("/chat/message")
def chat_message():
    return {"message": "Hello from IOPHA"}