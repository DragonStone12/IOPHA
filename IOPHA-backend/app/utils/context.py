# Backwards-compatible re-export. The canonical request-id context variable
# now lives in ``app.core.context``; this module keeps legacy imports working
# without forking the ContextVar (so the middleware, formatter, and handlers
# all read the same correlation id).
from app.core.context import generate_request_id, get_request_id, request_id_ctx

__all__ = ["get_request_id", "generate_request_id", "request_id_ctx"]
