import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

REASON_MAX = 500
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_DIGIT_COUNT = 10


class PatientDataSchema(BaseModel):
    """Rigid inbound contract for the patient intake profile pipeline.

    Enforces bounded, PHI-aware validation so malformed or oversized payloads
    are rejected at the API boundary before any business logic executes.
    ``model_config = ConfigDict(extra="forbid")`` keeps the contract rigid so
    no unplanned field can cross the API boundary.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full name of the submitting patient",
    )
    email: str = Field(
        ...,
        description="Valid communications target email format",
    )
    phone: str = Field(
        ...,
        description="10-digit primary telephone contact key",
    )
    reason: str | None = Field(
        default=None,
        max_length=REASON_MAX,
        description="Optional patient-provided intake reason context",
    )

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        if not EMAIL_PATTERN.match(value):
            raise ValueError("Invalid email format.")
        return value

    @field_validator("phone")
    @classmethod
    def validate_ten_digit_phone(cls, value: str) -> str:
        """Enforce clean text constraints over incoming phone attributes.

        Ensures that exactly 10 digits are supplied without characters or
        spacers. Non-digit characters are stripped before length validation
        so formatted inputs (e.g. ``(555) 123-4567``) are normalized.
        """
        cleaned = re.sub(r"\D", "", value)
        if len(cleaned) != PHONE_DIGIT_COUNT:
            raise ValueError("Phone number must contain exactly 10 numerical digits.")
        return cleaned


__all__ = ["PatientDataSchema"]
