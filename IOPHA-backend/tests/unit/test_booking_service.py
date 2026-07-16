from datetime import date

import pytest

from app.exceptions.timeslot_exceptions import (
    InvalidTimeSlotFormatException,
    ProviderNotFoundException,
    ScheduleLockConflictException,
    TimeSlotUnavailableException,
)
from app.repositories.booking_repository import InMemoryBookingRepository
from app.repositories.calendar_repository import (
    CalendarRepository,
    InMemoryCalendarRepository,
    TimeSlotRecord,
)
from app.repositories.provider_repository import InMemoryProviderRepository
from app.schemas import ProviderRecord
from app.schemas.patient.patient_data import PatientDataSchema
from app.services.booking_service import InMemoryBookingService


def _valid_patient() -> PatientDataSchema:
    return PatientDataSchema(
        name="Alex Stone",
        email="alex@example.com",
        phone="5551234567",
        reason="Initial Consultation",
    )


class _RaceCalendarRepository(CalendarRepository):
    """Simulates a race where get_slots shows available but reserve_slot fails."""

    def get_provider(self, provider_id: str) -> ProviderRecord | None:
        return ProviderRecord(
            id="prov-123",
            name="Dr. Test",
            specialty="General",
            distance="1.0 mi",
            rating=5.0,
            reviewCount=10,
            nextAvailable="Today",
            db_primary_key=1,
        )

    def get_slots(self, provider_id: str) -> list[TimeSlotRecord]:
        return [
            TimeSlotRecord(
                id=f"{date.today().isoformat()}-09:00 AM",
                time="09:00 AM",
                label="09:00 AM",
                available=True,
            )
        ]

    def reserve_slot(self, slot_id: str) -> bool:
        return False


class TestInMemoryBookingService:
    def test_creates_booking_for_available_slot(self) -> None:
        calendar_repo = InMemoryCalendarRepository()
        provider_repo = InMemoryProviderRepository()
        booking_repo = InMemoryBookingRepository()
        service = InMemoryBookingService(
            calendar_repository=calendar_repo,
            provider_repository=provider_repo,
            booking_repository=booking_repo,
        )

        today = date.today().isoformat()
        slots = calendar_repo.get_slots("prov-123")
        available_slot = next(slot for slot in slots if slot.available)

        response = service.create_booking(
            provider_id="prov-123",
            slot_id=available_slot.id,
            patient_data=_valid_patient(),
        )

        assert response.bookingId.startswith("bk-")
        assert response.summary.physician.id == "prov-123"
        assert response.summary.date.isoformat() == today
        assert response.summary.time == available_slot.time

    def test_rejects_invalid_slot_format(self) -> None:
        service = InMemoryBookingService(
            calendar_repository=InMemoryCalendarRepository(),
            provider_repository=InMemoryProviderRepository(),
            booking_repository=InMemoryBookingRepository(),
        )

        with pytest.raises(InvalidTimeSlotFormatException):
            service.create_booking(
                provider_id="prov-123",
                slot_id="not-a-slot",
                patient_data=_valid_patient(),
            )

    def test_rejects_unknown_provider(self) -> None:
        service = InMemoryBookingService(
            calendar_repository=InMemoryCalendarRepository(),
            provider_repository=InMemoryProviderRepository(),
            booking_repository=InMemoryBookingRepository(),
        )

        with pytest.raises(ProviderNotFoundException):
            service.create_booking(
                provider_id="missing-provider",
                slot_id=f"{date.today().isoformat()}-09:00 AM",
                patient_data=_valid_patient(),
            )

    def test_rejects_unavailable_slot(self) -> None:
        calendar_repo = InMemoryCalendarRepository()
        provider_repo = InMemoryProviderRepository()
        booking_repo = InMemoryBookingRepository()
        service = InMemoryBookingService(
            calendar_repository=calendar_repo,
            provider_repository=provider_repo,
            booking_repository=booking_repo,
        )

        slots = calendar_repo.get_slots("prov-123")
        unavailable_slot = next(slot for slot in slots if not slot.available)

        with pytest.raises(TimeSlotUnavailableException):
            service.create_booking(
                provider_id="prov-123",
                slot_id=unavailable_slot.id,
                patient_data=_valid_patient(),
            )

    def test_rejects_fabricated_slot_id(self) -> None:
        service = InMemoryBookingService(
            calendar_repository=InMemoryCalendarRepository(),
            provider_repository=InMemoryProviderRepository(),
            booking_repository=InMemoryBookingRepository(),
        )

        with pytest.raises(TimeSlotUnavailableException):
            service.create_booking(
                provider_id="prov-123",
                slot_id=f"{date.today().isoformat()}-11:45 PM",
                patient_data=_valid_patient(),
            )

    def test_reserving_already_reserved_slot_raises_unavailable(self) -> None:
        calendar_repo = InMemoryCalendarRepository()
        provider_repo = InMemoryProviderRepository()
        booking_repo = InMemoryBookingRepository()
        service = InMemoryBookingService(
            calendar_repository=calendar_repo,
            provider_repository=provider_repo,
            booking_repository=booking_repo,
        )

        slots = calendar_repo.get_slots("prov-123")
        available_slot = next(slot for slot in slots if slot.available)

        # First booking succeeds.
        service.create_booking(
            provider_id="prov-123",
            slot_id=available_slot.id,
            patient_data=_valid_patient(),
        )

        # Second booking on the same slot should fail as unavailable.
        with pytest.raises(TimeSlotUnavailableException):
            service.create_booking(
                provider_id="prov-123",
                slot_id=available_slot.id,
                patient_data=_valid_patient(),
            )

    def test_race_condition_raises_lock_conflict(self) -> None:
        service = InMemoryBookingService(
            calendar_repository=_RaceCalendarRepository(),
            provider_repository=InMemoryProviderRepository(),
            booking_repository=InMemoryBookingRepository(),
        )

        with pytest.raises(ScheduleLockConflictException):
            service.create_booking(
                provider_id="prov-123",
                slot_id=f"{date.today().isoformat()}-09:00 AM",
                patient_data=_valid_patient(),
            )
