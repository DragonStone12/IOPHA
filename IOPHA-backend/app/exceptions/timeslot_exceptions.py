import logging

from fastapi import status

from app.exceptions.domain_errors import IOPHADomainError


class AppBaseException(IOPHADomainError):  # noqa: N818
    """Base class for all Time Slot Availability API domain errors."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    link = "base"
    title = "Application Error"
    log_level = logging.ERROR
    log_event = "request.domain_error"


class TimeSlotUnavailableException(AppBaseException):
    """The requested appointment slot is no longer available for booking."""

    status_code = status.HTTP_409_CONFLICT
    link = "time-slot-unavailable"
    title = "Time Slot Unavailable"
    log_level = logging.WARNING
    log_event = "timeslot.unavailable"

    def __init__(self, slot_id: str) -> None:
        super().__init__()
        self.slot_id = slot_id

    def safe_detail(self) -> str:
        return (
            f"The requested time slot '{self.slot_id}' is no longer available. "
            "Please select a different time."
        )

    def log_context(self) -> dict[str, object]:
        return {"slotId": self.slot_id}


class ProviderNotFoundException(AppBaseException):
    """The requested provider was not found in the directory."""

    status_code = status.HTTP_404_NOT_FOUND
    link = "provider-not-found-error"
    title = "Provider Not Found"
    log_level = logging.WARNING
    log_event = "directory.provider_not_found"

    def __init__(self, provider_id: str) -> None:
        super().__init__()
        self.provider_id = provider_id

    def safe_detail(self) -> str:
        return (
            f"The requested provider '{self.provider_id}' was not found in the "
            "directory. Verify the provider ID and try again."
        )

    def log_context(self) -> dict[str, object]:
        return {"providerId": self.provider_id}


class InvalidTimeSlotFormatException(AppBaseException):
    """The supplied time slot identifier or time string does not conform."""

    status_code = status.HTTP_400_BAD_REQUEST
    link = "invalid-time-slot-format"
    title = "Invalid Time Slot Format"
    log_level = logging.WARNING
    log_event = "timeslot.invalid_format"

    def __init__(self, details: str) -> None:
        super().__init__()
        self.details = details

    def safe_detail(self) -> str:
        return (
            "The time slot format is invalid. Expected format: "
            "'YYYY-MM-DD-h:MM AM/PM'. "
            f"Details: {self.details}"
        )

    def log_context(self) -> dict[str, object]:
        return {"details": self.details}


class ScheduleLockConflictException(AppBaseException):
    """The selected slot was reserved by another transaction during confirmation."""

    status_code = status.HTTP_409_CONFLICT
    link = "schedule-lock-conflict"
    title = "Schedule Lock Conflict"
    log_level = logging.WARNING
    log_event = "scheduling.lock_conflict"

    def __init__(self, slot_id: str, provider_id: str) -> None:
        super().__init__()
        self.slot_id = slot_id
        self.provider_id = provider_id

    def safe_detail(self) -> str:
        return (
            f"The slot '{self.slot_id}' was just reserved by another patient. "
            "Please select a different time."
        )

    def log_context(self) -> dict[str, object]:
        return {"slotId": self.slot_id, "providerId": self.provider_id}


__all__ = [
    "AppBaseException",
    "InvalidTimeSlotFormatException",
    "ProviderNotFoundException",
    "ScheduleLockConflictException",
    "TimeSlotUnavailableException",
]
