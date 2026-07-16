import logging
from datetime import date

from app.exceptions.timeslot_exceptions import (
    InvalidTimeSlotFormatException,
    ProviderNotFoundException,
    ScheduleLockConflictException,
    TimeSlotUnavailableException,
)
from app.repositories.booking_repository import BookingRepository
from app.repositories.calendar_repository import CalendarRepository
from app.repositories.provider_repository import ProviderRepository
from app.schemas.booking import BookingResponseSchema, BookingSummarySchema
from app.schemas.patient.patient_data import PatientDataSchema
from app.schemas.provider.mappers import map_provider_to_physician
from app.schemas.timeslot import TimeSlotSchema

logger = logging.getLogger("iopha.backend")


def _slot_id_to_date_time(slot_id: str) -> tuple[date, str]:
    """Split a composite slot id into its ISO date and civil time parts.

    Assumes the slot id has already been validated against
    :attr:`TimeSlotSchema.SLOT_ID_PATTERN`.
    """
    # Format: YYYY-MM-DD-h:MM AM/PM
    iso_date = date.fromisoformat(slot_id[:10])
    time_part = slot_id[11:]
    return iso_date, time_part


class BookingService:
    """Business logic for the aggregate booking writer endpoint.

    Orchestrates provider lookup, slot validation/reservation, and booking
    persistence while ensuring no raw patient PII reaches log payloads.
    """

    def create_booking(
        self,
        provider_id: str,
        slot_id: str,
        patient_data: PatientDataSchema,
    ) -> BookingResponseSchema:
        """Attempt to commit a complete booking block."""
        raise NotImplementedError


class InMemoryBookingService(BookingService):
    """No-backend stand-in that coordinates in-memory repositories.

    Mirrors the intended transactional flow: validate provider, validate slot
    format, reserve the slot atomically, then persist the booking. When the
    calendar reservation fails (slot gone or race condition), a domain
    exception is raised so the global handler can return an RFC-7807 payload.
    """

    def __init__(
        self,
        calendar_repository: CalendarRepository,
        provider_repository: ProviderRepository,
        booking_repository: BookingRepository,
    ) -> None:
        self._calendar = calendar_repository
        self._providers = provider_repository
        self._bookings = booking_repository

    def create_booking(
        self,
        provider_id: str,
        slot_id: str,
        patient_data: PatientDataSchema,
    ) -> BookingResponseSchema:
        if not TimeSlotSchema.is_valid_slot_id(slot_id):
            raise InvalidTimeSlotFormatException(
                f"Slot id '{slot_id}' does not match expected format."
            )

        provider_record = self._providers.find_by_id(provider_id)
        if provider_record is None:
            raise ProviderNotFoundException(provider_id)

        provider_slots = self._calendar.get_slots(provider_id)
        matching_slot = next(
            (slot for slot in provider_slots if slot.id == slot_id), None
        )
        if matching_slot is None or not matching_slot.available:
            raise TimeSlotUnavailableException(slot_id)

        # Attempt the atomic reservation; a failure here indicates a race.
        if not self._calendar.reserve_slot(slot_id):
            raise ScheduleLockConflictException(slot_id, provider_id)

        appointment_date, appointment_time = _slot_id_to_date_time(slot_id)
        booking = self._bookings.create(
            provider_id=provider_id,
            slot_id=slot_id,
            date=appointment_date,
            time=appointment_time,
            patient_data=patient_data,
        )

        logger.info(
            "booking.created",
            extra={
                "extra_context": {
                    "path": "/api/bookings",
                    "bookingId": booking.id,
                    "providerId": provider_id,
                    "slotId": slot_id,
                }
            },
        )

        physician = map_provider_to_physician(provider_record)
        summary = BookingSummarySchema(
            physician=physician,
            date=appointment_date,
            time=appointment_time,
        )
        return BookingResponseSchema(bookingId=booking.id, summary=summary)


__all__ = [
    "BookingService",
    "InMemoryBookingService",
]
