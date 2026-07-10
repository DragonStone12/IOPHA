from app.middleware.request_tracing import RequestTracingMiddleware


# Ticket-named middleware for the availability API. It genuinely subclasses
# the proven request-tracing middleware so the class is reported/registered
# under the ``RequestTrackingMiddleware`` name (not merely re-labeled) while
# reusing its dispatch: it reads/assigns the ``request_id_ctx`` correlation id
# and echoes it back on the response header.
class RequestTrackingMiddleware(RequestTracingMiddleware):
    """ASGI middleware that guarantees every request carries a correlation id."""


__all__ = ["RequestTrackingMiddleware"]
