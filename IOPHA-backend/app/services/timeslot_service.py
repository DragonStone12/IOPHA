from app.exceptions.timeslot_exceptions import (
    InvalidTimeSlotFormatException,
    ProviderNotFoundException,
    TimeSlotUnavailableException,
)
from app.repositories.calendar_repository import CalendarRepository
from app.schemas.timeslot import TimeSlotSchema


class TimeSlotService:
    """Business logic for provider time-slot availability.

    Projects repository records into the external :class:`TimeSlotSchema`
    contract and raises domain-specific exceptions for invalid inputs and
    unavailable resources.
    """

    def __init__(self, repository: CalendarRepository) -> None:
        self._repository = repository

    def get_slots(self, provider_id: str) -> list[TimeSlotSchema]:
        """Return every calendar slot for *provider_id* as API DTOs."""
        if self._repository.get_provider(provider_id) is None:
            raise ProviderNotFoundException(provider_id)
        records = self._repository.get_slots(provider_id)
        return [
            TimeSlotSchema(
                id=record.id,
                time=record.time,
                label=record.label,
                available=record.available,
            )
            for record in records
        ]

    def reserve_slot(self, provider_id: str, slot_id: str) -> bool:
        """Attempt to reserve *slot_id* for *provider_id*.

        Validates the slot format and provider ownership before delegating.
        """
        if not TimeSlotSchema.is_valid_slot_id(slot_id):
            raise InvalidTimeSlotFormatException(
                f"Slot id '{slot_id}' does not match expected format."
            )
        if self._repository.get_provider(provider_id) is None:
            raise ProviderNotFoundException(provider_id)
        provider_slots = self._repository.get_slots(provider_id)
        if not any(record.id == slot_id for record in provider_slots):
            raise TimeSlotUnavailableException(slot_id)
        if not self._repository.reserve_slot(slot_id):
            raise TimeSlotUnavailableException(slot_id)
        return True


__all__ = ["TimeSlotService"]
