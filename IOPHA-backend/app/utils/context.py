import uuid
from contextvars import ContextVar

# Request correlation identifier threaded through every downstream operation
# (logging, repositories, services, background tasks) without being passed
# explicitly through function signatures. FastAPI/Starlette run the endpoint
# inside a task that inherits this context, so the value propagates
# automatically. Defaults to ``"system"`` when no request is active (e.g.
# unit tests that build LogRecords directly without an active request).
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="system")


def get_request_id() -> str:
    """Return the correlation id bound to the current execution context."""
    return request_id_ctx.get()


def generate_request_id() -> str:
    """Mint a new standard tracking UUID for an inbound request."""
    return str(uuid.uuid4())
