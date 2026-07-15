from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProblemDetail(BaseModel):
    """RFC 7807 problem-detail payload returned by every error path.

    Every fault (domain exception, validation error, or generic HTTP error)
    is projected into this single shape so clients can rely on a stable
    contract and copy the ``help_url`` straight into a browser to reach the
    relevant GitHub runbook. ``errors`` is an optional, scrubbed list of
    field-level validation failures (input values are deliberately omitted).
    """

    model_config = ConfigDict(extra="allow")

    title: str = Field(..., description="Short, human-readable summary of the problem.")
    status: int = Field(
        ..., description="HTTP status code generated for this response."
    )
    detail: str = Field(
        ...,
        description="Human-readable explanation specific to this occurrence.",
    )
    instance: str = Field(
        ..., description="URI reference identifying the request instance (path)."
    )
    help_url: str = Field(
        ...,
        description=(
            "Deep link into docs/RUNBOOKS.md describing remediation for this error."
        ),
    )
    requestId: Optional[str] = Field(
        default=None,
        description="Correlation ID tracing the request through the system.",
    )
    errors: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description=(
            "Scrubbed field-level validation failures "
            "(loc/msg/type only; input omitted)."
        ),
    )
