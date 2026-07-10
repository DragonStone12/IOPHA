from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, timedelta

from app.schemas import ProviderRecord

# Civil 12-hour clock labels produced for the booking UI, e.g. "09:00 AM".
_TIME_LABELS = [
    "09:00 AM",
    "09:30 AM",
    "10:00 AM",
    "10:30 AM",
    "11:00 AM",
    "11:30 AM",
    "01:00 PM",
    "01:30 PM",
    "02:00 PM",
    "02:30 PM",
    "03:00 PM",
    "03:30 PM",
]


@dataclass
class TimeSlotRecord:
    """Internal calendar representation before projection into the API DTO.

    This is the raw repository shape and may carry data that still needs
    format validation (the service layer rejects malformed ``id``/``time``
    strings before they become a :class:`TimeSlotSchema`).
    """

    id: str
    time: str
    label: str
    available: bool


class CalendarRepository(ABC):
    """Persistence boundary for provider availability lookups."""

    @abstractmethod
    def get_provider(self, provider_id: str) -> ProviderRecord | None:
        """Return the provider directory record, or ``None`` if absent."""

    @abstractmethod
    def get_slots(self, provider_id: str) -> list[TimeSlotRecord]:
        """Return the provider's calendar slots (may be empty)."""

    @abstractmethod
    def reserve_slot(self, slot_id: str) -> bool:
        """Attempt to reserve *slot_id*; return ``True`` on success."""


class InMemoryCalendarRepository(CalendarRepository):
    """Default no-database stand-in used until a real calendar is wired.

    Seeds a deterministic set of slots for a handful of known provider ids so
    the availability endpoint returns realistic data without external state.
    """

    def __init__(self, days_ahead: int = 7) -> None:
        self._days_ahead = days_ahead
        self._providers = {
            "prov-123": ProviderRecord(
                id="prov-123",
                name="Dr. Emily Chen, MD",
                specialty="Cardiology",
                distance="1.8 miles",
                rating=4.9,
                reviewCount=120,
                nextAvailable="Today, 3:30 PM",
                imageUrl="https://cdn.example.com/emily.jpg",
                facility="Northside Medical Center",
                db_primary_key=42,
            ),
        }
        # Slot ids that have been reserved and are no longer bookable.
        self._reserved: set[str] = set()
        # Every slot id this repository can actually produce, across all
        # seeded providers, so reservations can be validated for existence.
        self._valid_slot_ids: set[str] = {
            slot.id
            for provider_id in self._providers
            for slot in self._generate_slots(provider_id)
        }

    def get_provider(self, provider_id: str) -> ProviderRecord | None:
        return self._providers.get(provider_id)

    def get_slots(self, provider_id: str) -> list[TimeSlotRecord]:
        if provider_id not in self._providers:
            return []
        return self._generate_slots(provider_id)

    def _generate_slots(self, provider_id: str) -> list[TimeSlotRecord]:
        slots: list[TimeSlotRecord] = []
        for offset in range(self._days_ahead):
            day = date.today() + timedelta(days=offset)
            for index, label in enumerate(_TIME_LABELS):
                slot_id = f"{day.isoformat()}-{label}"
                # Every third slot is held/booked to mimic real availability.
                available = (index + offset) % 3 != 0 and slot_id not in self._reserved
                slots.append(
                    TimeSlotRecord(
                        id=slot_id,
                        time=label,
                        label=label,
                        available=available,
                    )
                )
        return slots

    def reserve_slot(self, slot_id: str) -> bool:
        # Reject fabricated or already-removed slot ids: a reservation is only
        # valid for a slot this repository actually vends.
        if slot_id not in self._valid_slot_ids or slot_id in self._reserved:
            return False
        self._reserved.add(slot_id)
        return True


__all__ = [
    "CalendarRepository",
    "InMemoryCalendarRepository",
    "TimeSlotRecord",
]
