# Backwards-compatible re-export. The canonical request-id context variable
# now lives in ``app.core.context``; this module keeps legacy imports working
# without forking the ContextVar (so the middleware, formatter, and handlers
# all read the same correlation id).
from app.core.context import (
    generate_request_id,
    get_request_id,
    preserve_request_context,
    request_id_ctx,
    run_with_request_context,
)

__all__ = [
    "generate_request_id",
    "get_request_id",
    "preserve_request_context",
    "request_id_ctx",
    "run_with_request_context",
]
