from app.middleware.request_tracing import RequestTracingMiddleware

# Ticket-named facade over the proven request-tracing middleware. The class
# reads/assigns the ``request_id_ctx`` correlation id (see app.core.context)
# and echoes it back on the response header. The implementation lives in
# ``app.middleware.request_tracing``; this module exposes it under the
# ``RequestTrackingMiddleware`` name required by the availability API spec.
RequestTrackingMiddleware = RequestTracingMiddleware

__all__ = ["RequestTrackingMiddleware"]
