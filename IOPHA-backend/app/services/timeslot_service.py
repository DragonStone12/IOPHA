from app.repositories.calendar_repository import CalendarRepository
from app.schemas.timeslot import TimeSlotSchema


class TimeSlotService:
    """Business logic for provider time-slot availability.

    Projects repository records into the external :class:`TimeSlotSchema`
    contract. Domain faults (unknown provider, unavailable slot, malformed
    slot format) are introduced in later parts of this feature; for the
    contract layer the service simply adapts the repository result.
    """

    def __init__(self, repository: CalendarRepository) -> None:
        self._repository = repository

    def get_slots(self, provider_id: str) -> list[TimeSlotSchema]:
        """Return every calendar slot for *provider_id* as API DTOs."""
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

    def reserve_slot(self, slot_id: str) -> bool:
        """Attempt to reserve *slot_id*; delegate to the repository."""
        return self._repository.reserve_slot(slot_id)


__all__ = ["TimeSlotService"]
