import pytest
from pydantic import ValidationError

from app.schemas.tip import TipSchema


def _valid_tip() -> dict[str, object]:
    return {
        "id": "tip-001",
        "number": 1,
        "title": "Hydrate Early",
        "description": "Drink plenty of water throughout the day.",
    }


class TestTipSchemaValidation:
    def test_accepts_well_formed_tip(self) -> None:
        tip = TipSchema(**_valid_tip())  # type: ignore[arg-type]
        assert tip.id == "tip-001"
        assert tip.number == 1
        assert tip.title == "Hydrate Early"
        assert tip.description == "Drink plenty of water throughout the day."

    def test_id_is_optional(self) -> None:
        payload = _valid_tip()
        payload.pop("id")
        tip = TipSchema(**payload)  # type: ignore[arg-type]
        assert tip.id is None

    @pytest.mark.parametrize("bad_number", [0, -1, -100])
    def test_rejects_non_positive_number(self, bad_number: int) -> None:
        payload = {**_valid_tip(), "number": bad_number}
        with pytest.raises(ValidationError):
            TipSchema(**payload)  # type: ignore[arg-type]

    @pytest.mark.parametrize("bad_number", ["one", 1.5, None])
    def test_rejects_non_integer_number(self, bad_number: object) -> None:
        payload = {**_valid_tip(), "number": bad_number}
        with pytest.raises(ValidationError):
            TipSchema(**payload)  # type: ignore[arg-type]

    @pytest.mark.parametrize("field", ["title", "description"])
    def test_rejects_empty_text_fields(self, field: str) -> None:
        payload = {**_valid_tip(), field: ""}
        with pytest.raises(ValidationError):
            TipSchema(**payload)  # type: ignore[arg-type]

    def test_rejects_title_exceeds_max_length(self) -> None:
        payload = {**_valid_tip(), "title": "x" * 201}
        with pytest.raises(ValidationError):
            TipSchema(**payload)  # type: ignore[arg-type]

    def test_rejects_description_exceeds_max_length(self) -> None:
        payload = {**_valid_tip(), "description": "x" * 2001}
        with pytest.raises(ValidationError):
            TipSchema(**payload)  # type: ignore[arg-type]

    @pytest.mark.parametrize("missing", ["number", "title", "description"])
    def test_rejects_missing_required_field(self, missing: str) -> None:
        payload = _valid_tip()
        payload.pop(missing)
        with pytest.raises(ValidationError):
            TipSchema(**payload)  # type: ignore[arg-type]

    def test_rejects_unknown_field(self) -> None:
        payload = {**_valid_tip(), "ssn": "123-45-6789"}
        with pytest.raises(ValidationError):
            TipSchema(**payload)  # type: ignore[arg-type]

    def test_serializes_to_expected_json(self) -> None:
        tip = TipSchema(**_valid_tip())  # type: ignore[arg-type]
        assert tip.model_dump() == _valid_tip()

    def test_serializes_without_id(self) -> None:
        payload = _valid_tip()
        payload.pop("id")
        tip = TipSchema(**payload)  # type: ignore[arg-type]
        assert tip.id is None
        dumped = tip.model_dump()
        assert dumped["id"] is None
        assert dumped["number"] == 1
        assert dumped["title"] == "Hydrate Early"
        assert dumped["description"] == "Drink plenty of water throughout the day."
