from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.timeslot import TimeSlotSchema

TODAY = date.today().isoformat()


def _valid_slot() -> dict[str, object]:
    return {
        "id": f"{TODAY}-09:00 AM",
        "time": "09:00 AM",
        "label": "09:00 AM",
        "available": True,
    }


class TestTimeSlotSchemaValidation:
    def test_accepts_well_formed_slot(self) -> None:
        slot = TimeSlotSchema(**_valid_slot())  # type: ignore[arg-type]
        assert slot.id == f"{TODAY}-09:00 AM"
        assert slot.time == "09:00 AM"
        assert slot.available is True

    def test_accepts_pm_time(self) -> None:
        payload = {**_valid_slot(), "time": "02:30 PM", "id": f"{TODAY}-02:30 PM"}
        slot = TimeSlotSchema(**payload)  # type: ignore[arg-type]
        assert slot.time == "02:30 PM"

    def test_accepts_unavailable_flag(self) -> None:
        payload = {**_valid_slot(), "available": False}
        slot = TimeSlotSchema(**payload)  # type: ignore[arg-type]
        assert slot.available is False

    @pytest.mark.parametrize(
        "bad_time",
        ["9:00 AM", "09:00", "25:00 AM", "09:60 PM", "9:5 am", "noon"],
    )
    def test_rejects_malformed_time(self, bad_time: str) -> None:
        payload = {**_valid_slot(), "time": bad_time, "id": f"{TODAY}-{bad_time}"}
        with pytest.raises(ValidationError):
            TimeSlotSchema(**payload)  # type: ignore[arg-type]

    def test_rejects_malformed_slot_id(self) -> None:
        payload = {**_valid_slot(), "id": "not-a-valid-id"}
        with pytest.raises(ValidationError):
            TimeSlotSchema(**payload)  # type: ignore[arg-type]

    def test_rejects_slot_id_with_wrong_separator(self) -> None:
        # A pattern only validates *format*, not real calendar dates; a bad
        # separator (slash instead of dash) must still be rejected.
        payload = {**_valid_slot(), "id": "2024/01/15-09:00 AM"}
        with pytest.raises(ValidationError):
            TimeSlotSchema(**payload)  # type: ignore[arg-type]

    def test_rejects_unknown_field(self) -> None:
        payload = {**_valid_slot(), "ssn": "123-45-6789"}
        with pytest.raises(ValidationError):
            TimeSlotSchema(**payload)  # type: ignore[arg-type]

    @pytest.mark.parametrize("missing", ["id", "time", "label", "available"])
    def test_rejects_missing_required_field(self, missing: str) -> None:
        payload = _valid_slot()
        payload.pop(missing)
        with pytest.raises(ValidationError):
            TimeSlotSchema(**payload)  # type: ignore[arg-type]

    def test_rejects_label_exceeds_max_length(self) -> None:
        payload = {**_valid_slot(), "label": "x" * 101}
        with pytest.raises(ValidationError):
            TimeSlotSchema(**payload)  # type: ignore[arg-type]

    def test_pattern_helpers(self) -> None:
        assert TimeSlotSchema.is_valid_time("11:30 AM")
        assert not TimeSlotSchema.is_valid_time("11:30")
        assert TimeSlotSchema.is_valid_slot_id(f"{TODAY}-11:30 AM")
        assert not TimeSlotSchema.is_valid_slot_id("11:30 AM")
