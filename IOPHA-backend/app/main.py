from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.controllers.providers import router as providers_router
from app.middleware import RequestTracingMiddleware
from app.utils.handlers import ProblemAPIRoute, register_exception_handlers
from app.utils.logging import CentralizedLoggingMiddleware, configure_logging

app = FastAPI(title="IOPHA Backend API", route_class=ProblemAPIRoute)

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


def _build_openapi() -> dict[str, object]:
    """Generate the OpenAPI schema with the true RFC-7807 error contract.

    FastAPI auto-documents 422 faults with the default ``HTTPValidationError``
    schema. We rewrite every 422 response to reference ``ProblemDetail`` and
    register that schema, so the published contract matches the real error
    object (including the ``help_url`` runbook link) that clients receive.
    """
    if getattr(app, "openapi_schema", None):
        return app.openapi_schema  # type: ignore[return-value]
    from fastapi.openapi.utils import get_openapi

    from app.schemas.problem.problem_detail import ProblemDetail

    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    problem = ProblemDetail.model_json_schema(
        ref_template="#/components/schemas/{model}"
    )
    definitions = problem.pop("$defs", {})
    components = schema.setdefault("components", {})
    components_schemas = components.setdefault("schemas", {})
    components_schemas["ProblemDetail"] = problem
    components_schemas.update(definitions)
    # Drop the now-unused default validation schemas.
    components_schemas.pop("HTTPValidationError", None)
    components_schemas.pop("ValidationError", None)

    for path in schema.get("paths", {}).values():
        for operation in path.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses", {})
            if "422" in responses:
                responses["422"] = {
                    "description": (
                        "Request validation failed (RFC 7807 problem detail)."
                    ),
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                        }
                    },
                }
    app.openapi_schema = schema
    return schema


app.openapi = _build_openapi  # type: ignore[assignment]
