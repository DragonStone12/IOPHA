from datetime import date

import pytest

from app.exceptions.timeslot_exceptions import TimeSlotUnavailableException
from app.repositories.calendar_repository import InMemoryCalendarRepository
from app.services.timeslot_service import TimeSlotService


def _known_slot_id(repo: InMemoryCalendarRepository) -> str:
    return next(iter(repo._valid_slot_ids))


class TestInMemoryCalendarRepository:
    def test_get_provider_returns_seeded_record(self) -> None:
        repo = InMemoryCalendarRepository()
        record = repo.get_provider("prov-123")
        assert record is not None
        assert record.id == "prov-123"

    def test_get_provider_returns_none_for_unknown(self) -> None:
        repo = InMemoryCalendarRepository()
        assert repo.get_provider("ghost") is None

    def test_get_slots_empty_for_unknown_provider(self) -> None:
        repo = InMemoryCalendarRepository()
        assert repo.get_slots("ghost") == []

    def test_get_slots_returns_valid_schemas(self) -> None:
        repo = InMemoryCalendarRepository()
        slots = repo.get_slots("prov-123")
        assert len(slots) > 0
        for slot in slots:
            # id embeds today/upcoming ISO date + civil time.
            assert slot.id.startswith(date.today().isoformat()[:4])
            assert slot.time in slot.id

    def test_reserve_slot_succeeds_for_valid_id(self) -> None:
        repo = InMemoryCalendarRepository()
        slot_id = _known_slot_id(repo)
        assert repo.reserve_slot(slot_id) is True

    def test_reserve_slot_rejects_unknown_id(self) -> None:
        repo = InMemoryCalendarRepository()
        assert repo.reserve_slot("2099-01-01-09:00 AM") is False

    def test_reserve_slot_rejects_fabricated_id(self) -> None:
        repo = InMemoryCalendarRepository()
        assert repo.reserve_slot("not-a-slot-id") is False

    def test_reserve_slot_is_idempotent_false_on_second_call(self) -> None:
        repo = InMemoryCalendarRepository()
        slot_id = _known_slot_id(repo)
        assert repo.reserve_slot(slot_id) is True
        assert repo.reserve_slot(slot_id) is False


class TestTimeSlotService:
    def test_get_slots_returns_projected_schemas(self) -> None:
        service = TimeSlotService(InMemoryCalendarRepository())
        slots = service.get_slots("prov-123")
        assert len(slots) > 0
        assert all(slot.available in (True, False) for slot in slots)
        assert slots[0].id.endswith(slots[0].time)

    def test_reserve_slot_delegates_to_repository(self) -> None:
        repo = InMemoryCalendarRepository()
        service = TimeSlotService(repo)
        slot_id = _known_slot_id(repo)
        assert service.reserve_slot("prov-123", slot_id) is True
        with pytest.raises(TimeSlotUnavailableException):
            service.reserve_slot("prov-123", slot_id)
