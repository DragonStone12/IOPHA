import logging
from typing import Any

from aws_lambda_powertools import Metrics, single_metric
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.metrics.provider import cold_start
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.controllers.booking import router as booking_router
from app.controllers.intake import router as intake_router
from app.controllers.nutrition import router as nutrition_router
from app.controllers.providers import router as providers_router
from app.controllers.providers_search import router as providers_search_router
from app.controllers.timeslots import router as timeslots_router
from app.controllers.tips import router as tips_router
from app.core.config import settings
from app.core.logging_config import configure_structured_logging
from app.exceptions.error_handlers import register_timeslot_error_handlers
from app.middleware.metrics import MetricsMiddleware
from app.middleware.tracking import RequestTrackingMiddleware
from app.utils.handlers import ProblemAPIRoute, register_exception_handlers
from app.utils.logging import CentralizedLoggingMiddleware

app = FastAPI(title="IOPHA Backend API", route_class=ProblemAPIRoute)

register_exception_handlers(app)
register_timeslot_error_handlers(app)

logger = configure_structured_logging(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
)
# Shared Powertools metrics registry. EMF JSON is written to stdout on flush;
# the Lambda Runtime API ships it to CloudWatch Metrics automatically.
metrics = Metrics(
    namespace=settings.POWERTOOLS_METRICS_NAMESPACE,
    service=settings.POWERTOOLS_SERVICE_NAME,
)
app.add_middleware(CentralizedLoggingMiddleware, logger=logger)
# MetricsMiddleware runs inside RequestTrackingMiddleware so the correlation
# id is bound for the request lifetime when metrics are recorded.
app.add_middleware(MetricsMiddleware, metrics=metrics)
app.add_middleware(RequestTrackingMiddleware)
app.include_router(providers_router)
app.include_router(providers_search_router)
app.include_router(timeslots_router)
app.include_router(tips_router)
app.include_router(nutrition_router)
app.include_router(intake_router)
app.include_router(booking_router)

# Prometheus pull/scrape instrumentation is local-dev only. Lambda containers
# are ephemeral (no persistent IP/port), so the /metrics endpoint is
# unscrapable in production and stays disabled unless explicitly opted in.
if settings.PROMETHEUS_ENABLED:
    from prometheus_fastapi_instrumentator import Instrumentator

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

    from app.schemas.booking import (
        BookingResponseSchema,
        CalendarSlotsResponseSchema,
    )
    from app.schemas.find_doctor import FindDoctorResponseDataSchema
    from app.schemas.nutrition_response import NutritionResponseDataSchema
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
    components_schemas["NutritionResponseDataSchema"] = (
        NutritionResponseDataSchema.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
    )
    components_schemas["BookingResponseSchema"] = (
        BookingResponseSchema.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
    )
    components_schemas["CalendarSlotsResponseSchema"] = (
        CalendarSlotsResponseSchema.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
    )

    response_overrides: list[tuple[str, str, int, dict[str, object]]] = [
        (
            "/api/providers/{provider_id}",
            "get",
            404,
            {
                "description": (
                    "Provider record was not found (ProviderNotFoundException)"
                ),
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                    }
                },
            },
        ),
        (
            "/api/tips/{tip_id}",
            "get",
            404,
            {
                "description": "Tip record was not found (TipNotFoundException)",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                    }
                },
            },
        ),
        (
            "/api/patients/intake",
            "post",
            422,
            {
                "description": (
                    "Intake validation or processing failed "
                    "(RequestValidationError or IntakeProcessingException)"
                ),
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                    }
                },
            },
        ),
        (
            "/api/providers/search",
            "post",
            200,
            {
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
            },
        ),
        (
            "/api/nutrition/evaluate",
            "post",
            200,
            {
                "description": (
                    "Nutrition response with exactly 3 tips and an "
                    "optional physician recommendation."
                ),
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": ("#/components/schemas/NutritionResponseDataSchema")
                        }
                    }
                },
            },
        ),
        (
            "/api/patients/intake",
            "post",
            200,
            {
                "description": "Intake profile processed successfully.",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "status": {"type": "string"},
                                "id": {"type": "string"},
                            },
                        }
                    }
                },
            },
        ),
        (
            "/api/providers/{provider_id}/slots",
            "get",
            200,
            {
                "description": ("Day-scoped calendar availability for the provider."),
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": ("#/components/schemas/CalendarSlotsResponseSchema")
                        }
                    }
                },
            },
        ),
        (
            "/api/bookings",
            "post",
            201,
            {
                "description": "Booking created successfully.",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/BookingResponseSchema"}
                    }
                },
            },
        ),
    ]

    for path_key, path in schema.get("paths", {}).items():
        for operation in path.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses", {})
            if "422" in responses:
                responses["422"] = {
                    "description": (
                        "The request payload validation failed (RequestValidationError)"
                    ),
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                        }
                    },
                }
            for override_path, method, status_code, override in response_overrides:
                if path_key == override_path and method in path:
                    responses[str(status_code)] = override
    app.openapi_schema = schema
    return schema


app.openapi = _build_openapi  # type: ignore[method-assign]


# Strict CORS restricted to the deployed Amplify frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://main.d25f7ihio0gzb6.amplifyapp.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "message": "Backend is reachable"}


# AWS Lambda entry point. lifespan="off" prevents connection-pool exhaustion
# when Lambda execution contexts freeze and thaw between invocations.
_mangum_handler = Mangum(app, lifespan="off")


def _emit_cold_start_metric() -> None:
    """Emit a one-off ``ColdStart`` EMF metric via Powertools ``single_metric``.

    ``single_metric`` is dimension- and namespace-isolated from the shared
    request-metrics registry, so the cold-start blob never interferes with
    per-request flushes.
    """
    if not settings.METRICS_ENABLED:
        return
    with single_metric(
        name="ColdStart",
        unit=MetricUnit.Count,
        value=1,
        namespace=settings.POWERTOOLS_METRICS_NAMESPACE,
        default_dimensions={"service": settings.POWERTOOLS_SERVICE_NAME},
    ):
        pass


def handler(event: dict[str, Any], context: Any) -> Any:
    """Lambda entry point: Mangum wrapper plus cold-start metric emission.

    Powertools tracks execution-environment initialization in
    ``cold_start.is_cold_start``; the metric is emitted exactly once per
    environment, on the first invocation.
    """
    if cold_start.is_cold_start:
        cold_start.is_cold_start = False
        _emit_cold_start_metric()
    return _mangum_handler(event, context)
