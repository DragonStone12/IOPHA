from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.controllers.providers import router as providers_router
from app.controllers.providers_search import router as providers_search_router
from app.controllers.timeslots import router as timeslots_router
from app.controllers.tips import router as tips_router
from app.core.logging_config import configure_structured_logging
from app.exceptions.error_handlers import register_timeslot_error_handlers
from app.middleware.tracking import RequestTrackingMiddleware
from app.utils.handlers import ProblemAPIRoute, register_exception_handlers
from app.utils.logging import CentralizedLoggingMiddleware

app = FastAPI(title="IOPHA Backend API", route_class=ProblemAPIRoute)

register_exception_handlers(app)
register_timeslot_error_handlers(app)

logger = configure_structured_logging()
app.add_middleware(CentralizedLoggingMiddleware, logger=logger)
app.add_middleware(RequestTrackingMiddleware)
app.include_router(providers_router)
app.include_router(providers_search_router)
app.include_router(timeslots_router)
app.include_router(tips_router)

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

    from app.schemas.find_doctor import FindDoctorResponseDataSchema
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
    components_schemas.pop("HTTPValidationError", None)
    components_schemas.pop("ValidationError", None)

    components_schemas["FindDoctorResponseDataSchema"] = (
        FindDoctorResponseDataSchema.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
    )

    for path_key, path in schema.get("paths", {}).items():
        for operation in path.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses", {})
            if "422" in responses:
                responses["422"] = {
                    "description": (
                        "Request payload validation failed "
                        "(Unprocessable Entity Exception)"
                    ),
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                        }
                    },
                }
            if path_key == "/api/providers/{provider_id}" and "get" in path:
                responses["404"] = {
                    "description": (
                        "Provider record not found (ProviderNotFoundException)."
                    ),
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                        }
                    },
                }
            if path_key == "/api/tips/{tip_id}" and "get" in path:
                responses["404"] = {
                    "description": ("Tip record not found (TipNotFoundException)."),
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                        }
                    },
                }
            if path_key == "/api/v1/providers/search" and "post" in path:
                responses["200"] = {
                    "description": (
                        "Discovery result with providers and follow-up actions."
                    ),
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": (
                                    "#/components/schemas/FindDoctorResponseDataSchema"
                                )
                            }
                        }
                    },
                }
    app.openapi_schema = schema
    return schema


app.openapi = _build_openapi  # type: ignore[method-assign]
