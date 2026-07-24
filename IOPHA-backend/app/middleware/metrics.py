import re
import time
from collections.abc import Awaitable
from typing import Any, Callable

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from app.core.config import settings

# SECURITY.md mandates the ``[^/]+`` rule (never ``\d+``) so numeric IDs,
# UUIDs, and slugs are ALL normalised before a path may be used as a
# CloudWatch metric dimension. Here it matches FastAPI path-parameter
# placeholders (``{provider_id}``) inside matched route templates.
_PATH_PARAM = re.compile(r"\{[^/]+\}")

# Dimension value used when no route template matched (e.g. 404s). The raw
# path is never used as a fallback: it would leak unbounded identifiers
# (and potentially PHI) into an indexed CloudWatch dimension.
UNMATCHED_ROUTE = "unmatched"


def sanitize_route_template(template: str) -> str:
    """Collapse every FastAPI path parameter to a uniform ``{id}`` placeholder.

    Matched route templates carry real parameter names
    (``/api/providers/{provider_id}/slots``). Parameter names contain no PHI,
    but normalising them to ``{id}`` yields one stable, low-cardinality
    dimension value per route shape.
    """
    return _PATH_PARAM.sub("{id}", template)


def resolve_route_template(request: Request) -> str:
    """Return the sanitised route template for *request*.

    The matched FastAPI route (``scope["route"]``) supplies the templated
    path, so raw identifiers never reach a metric dimension. Requests that
    match no route collapse to :data:`UNMATCHED_ROUTE`.
    """
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if not isinstance(path, str) or not path:
        return UNMATCHED_ROUTE
    return sanitize_route_template(path)


def status_class(status_code: int) -> str:
    """Group a status code into its class bucket (``2xx``, ``4xx``, ...)."""
    return f"{status_code // 100}xx"


class MetricsMiddleware(BaseHTTPMiddleware):
    """Emit CloudWatch EMF core metrics for every HTTP request.

    Registered inside ``RequestTrackingMiddleware`` so the request
    correlation id is already bound for downstream logs. Emits
    ``RequestCount``, ``Latency`` (ms), and ``ErrorCount`` (5xx only) with
    dimensions ``[service, route_template, status_class]`` via AWS Lambda
    Powertools. Powertools writes EMF JSON to stdout, which the Lambda
    Runtime API extracts into CloudWatch Metrics -- no scraper, sidecar,
    Pushgateway, or extra IAM permissions required.
    """

    def __init__(self, app: Any, metrics: Metrics) -> None:
        super().__init__(app)
        self.metrics = metrics

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            self._record(request, 500, _elapsed_ms(start))
            raise
        self._record(request, response.status_code, _elapsed_ms(start))
        return response

    def _record(self, request: Request, status_code: int, duration_ms: float) -> None:
        if not settings.METRICS_ENABLED:
            return
        # Bind this request's dimensions to the current flush's dimension
        # set: unlike ``set_default_dimensions`` these do not persist across
        # requests -- ``flush_metrics`` clears them, so no stale values (or
        # Powertools overwrite warnings) leak into the next request.
        self.metrics.dimension_set["route_template"] = resolve_route_template(request)
        self.metrics.dimension_set["status_class"] = status_class(status_code)
        self.metrics.add_metric(name="RequestCount", unit=MetricUnit.Count, value=1)
        self.metrics.add_metric(
            name="Latency",
            unit=MetricUnit.Milliseconds,
            value=round(duration_ms, 2),
        )
        if status_code >= HTTP_500_INTERNAL_SERVER_ERROR:
            self.metrics.add_metric(name="ErrorCount", unit=MetricUnit.Count, value=1)
        self.metrics.flush_metrics()


def _elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000


__all__ = [
    "MetricsMiddleware",
    "UNMATCHED_ROUTE",
    "resolve_route_template",
    "sanitize_route_template",
    "status_class",
]
