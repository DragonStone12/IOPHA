from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from uuid import uuid4

from app.schemas.patient.patient_data import PatientDataSchema


@dataclass
class BookingRecord:
    """Internal persistence shape for a confirmed booking.

    Carries the opaque provider/slot identifiers plus the raw patient payload.
    The patient payload is never serialized to client responses; it is kept
    internal for downstream processing (confirmation emails, EHR writes, etc.).
    """

    id: str
    provider_id: str
    slot_id: str
    date: date
    time: str
    patient_data: PatientDataSchema
    metadata: dict[str, object] = field(default_factory=dict)


class BookingRepository(ABC):
    """Persistence boundary for confirmed bookings."""

    @abstractmethod
    def create(
        self,
        provider_id: str,
        slot_id: str,
        date: date,
        time: str,
        patient_data: PatientDataSchema,
    ) -> BookingRecord:
        """Persist a new confirmed booking and return its internal record."""

    @abstractmethod
    def get_by_id(self, booking_id: str) -> BookingRecord | None:
        """Return a booking by opaque id, or ``None`` if absent."""


class InMemoryBookingRepository(BookingRepository):
    """Default no-database stand-in used until a real datastore is wired."""

    def __init__(self) -> None:
        self._store: dict[str, BookingRecord] = {}

    def create(
        self,
        provider_id: str,
        slot_id: str,
        date: date,
        time: str,
        patient_data: PatientDataSchema,
    ) -> BookingRecord:
        booking_id = f"bk-{uuid4().hex[:12]}"
        record = BookingRecord(
            id=booking_id,
            provider_id=provider_id,
            slot_id=slot_id,
            date=date,
            time=time,
            patient_data=patient_data,
        )
        self._store[booking_id] = record
        return record

    def get_by_id(self, booking_id: str) -> BookingRecord | None:
        return self._store.get(booking_id)


__all__ = [
    "BookingRecord",
    "BookingRepository",
    "InMemoryBookingRepository",
]
