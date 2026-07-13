import re

from pydantic import BaseModel, ConfigDict, Field

# Time strings are displayed in 12-hour civil format with a zero-padded hour,
# e.g. "09:00 AM" or "02:30 PM". The slot id embeds an ISO calendar date
# followed by the same time token so a single slot is uniquely addressable
# across a provider's calendar (matches the frontend `TimeSlot.id` contract in
# IOPHA-frontend/src/components/booking/TimeSelector.tsx).
_TIME_CORE = r"(0[1-9]|1[0-2]):[0-5][0-9] (AM|PM)"
TIME_PATTERN = r"^" + _TIME_CORE + r"$"
SLOT_ID_PATTERN = r"^\d{4}-\d{2}-\d{2}-" + _TIME_CORE + r"$"


class TimeSlotSchema(BaseModel):
    """External time-slot contract returned by the availability API.

    Mirrors the `TimeSlot` interface consumed by the booking UI. The `id`
    embeds the calendar date and the civil time so the client can correlate a
    selected slot back to a specific provider calendar entry without extra
    lookups. Time and id are both validated against strict patterns so a
    malformed slot can never cross the API boundary (the service layer raises
    :class:`InvalidTimeSlotFormatException` on mismatch).
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        ...,
        pattern=SLOT_ID_PATTERN,
        description="Unique slot key: ISO date + civil time (YYYY-MM-DD-h:MM AM/PM).",
        examples=["2024-01-15-09:00 AM"],
    )
    time: str = Field(
        ...,
        pattern=TIME_PATTERN,
        description="Display time in 12-hour civil format (h:MM AM/PM).",
        examples=["09:00 AM"],
    )
    label: str = Field(
        ...,
        max_length=100,
        description="Human-readable label rendered on the slot button.",
        examples=["09:00 AM"],
    )
    available: bool = Field(
        ...,
        description="Whether the slot can still be booked by the patient.",
    )

    @classmethod
    def is_valid_time(cls, value: str) -> bool:
        """Return ``True`` only if *value* matches the civil time pattern."""
        return bool(re.match(TIME_PATTERN, value))

    @classmethod
    def is_valid_slot_id(cls, value: str) -> bool:
        """Return ``True`` only if *value* matches the composite slot id pattern."""
        return bool(re.match(SLOT_ID_PATTERN, value))
