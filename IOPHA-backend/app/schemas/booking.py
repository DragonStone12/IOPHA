import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.patient.patient_data import PatientDataSchema
from app.schemas.physician.physician_schema import PhysicianSchema
from app.schemas.timeslot import TimeSlotSchema


class CalendarSlotsResponseSchema(BaseModel):
    """Day-scoped schedule discovery response for a single provider.

    Mirrors the calendar/time-selection UI state: a target date plus every
    calendar node (available or booked) for that provider on that day.
    """

    model_config = ConfigDict(extra="forbid")

    date: datetime.date = Field(
        ...,
        description="Target query date formatted as YYYY-MM-DD",
    )
    slots: List[TimeSlotSchema] = Field(
        ...,
        description="Array of historical and active calendar node availabilities",
    )


class BookingRequestSchema(BaseModel):
    """Composite transactional payload for committing a complete booking block."""

    model_config = ConfigDict(extra="forbid")

    providerId: str = Field(
        ...,
        description="Target provider entity reference identifier",
    )
    slotId: str = Field(
        ...,
        description="Selected time slot allocation block key",
    )
    patientData: PatientDataSchema = Field(
        ...,
        description="Nested structural PII/PHI intake attributes validation sub-block",
    )


class BookingSummarySchema(BaseModel):
    """Sanitized, frontend-facing summary of the confirmed appointment."""

    model_config = ConfigDict(extra="forbid")

    physician: PhysicianSchema = Field(
        ...,
        description="Sanitized provider profile summary mapping",
    )
    date: datetime.date = Field(
        ...,
        description="Confirmed appointment date component",
    )
    time: str = Field(
        ...,
        description="Display format of the confirmed slot time, e.g., '04:00 PM'",
    )


class BookingResponseSchema(BaseModel):
    """Structured output for a successful booking creation."""

    model_config = ConfigDict(extra="forbid")

    bookingId: str = Field(
        ...,
        description="Centralized database reservation primary key reference",
    )
    summary: BookingSummarySchema = Field(
        ...,
        description="Nested metadata block characterizing the confirmed event",
    )


__all__ = [
    "BookingRequestSchema",
    "BookingResponseSchema",
    "BookingSummarySchema",
    "CalendarSlotsResponseSchema",
]
