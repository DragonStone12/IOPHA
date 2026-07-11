from datetime import date

from app.repositories.calendar_repository import TimeSlotRecord
from app.schemas import ProviderRecord


class MockCalendarService:
    """Fault-injectable calendar repository for isolated tests.

    Implements the :class:`CalendarRepository` interface with configurable
    success/failure paths so tests can exercise domain exceptions without
    touching any external calendar backend.
    """

    def __init__(  # noqa: PLR0913
        self,
        slots: list[TimeSlotRecord] | None = None,
        provider: ProviderRecord | None = None,
        reserve_succeeds: bool = True,
        raise_on_get_provider: type[Exception] | None = None,
        raise_on_get_slots: type[Exception] | None = None,
        raise_on_reserve: type[Exception] | None = None,
    ) -> None:
        self._slots = slots or [
            TimeSlotRecord(
                id=f"{date.today().isoformat()}-09:00 AM",
                time="09:00 AM",
                label="09:00 AM",
                available=True,
            )
        ]
        self._provider = provider or ProviderRecord(
            id="prov-123",
            name="Dr. Test",
            specialty="General",
            distance="1.0 mi",
            rating=5.0,
            reviewCount=10,
            nextAvailable="Today",
            imageUrl=None,
            facility=None,
            db_primary_key=1,
        )
        self._reserve_succeeds = reserve_succeeds
        self._raise_on_get_provider = raise_on_get_provider
        self._raise_on_get_slots = raise_on_get_slots
        self._raise_on_reserve = raise_on_reserve
        self._reserved: set[str] = set()

    @property
    def first_slot_id(self) -> str:
        """Return the id of the first seeded slot (for test convenience)."""
        return self._slots[0].id

    def get_provider(self, provider_id: str) -> ProviderRecord | None:
        if self._raise_on_get_provider is not None:
            raise self._raise_on_get_provider(provider_id)
        if self._provider and self._provider.id == provider_id:
            return self._provider
        return None

    def get_slots(self, provider_id: str) -> list[TimeSlotRecord]:
        if self._raise_on_get_slots is not None:
            raise self._raise_on_get_slots(provider_id)
        if self.get_provider(provider_id) is None:
            return []
        return [slot for slot in self._slots if slot.id not in self._reserved]

    def reserve_slot(self, slot_id: str) -> bool:
        if self._raise_on_reserve is not None:
            raise self._raise_on_reserve(slot_id)
        if not self._reserve_succeeds:
            return False
        if slot_id not in {slot.id for slot in self._slots}:
            return False
        self._reserved.add(slot_id)
        return True
