import pytest
from pydantic import ValidationError

from app.schemas.patient.patient_data import PatientDataSchema


def _valid_payload() -> dict:
    return {
        "name": "Alex Stone",
        "email": "alex@example.com",
        "phone": "5551234567",
        "reason": "Initial Consultation",
    }


class TestPatientDataSchemaValidation:
    def test_accepts_valid_payload(self) -> None:
        payload = PatientDataSchema(**_valid_payload())
        assert payload.name == "Alex Stone"
        assert payload.email == "alex@example.com"
        assert payload.phone == "5551234567"
        assert payload.reason == "Initial Consultation"

    def test_rejects_unknown_field(self) -> None:
        data = _valid_payload()
        data["intakeSource"] = "web"
        with pytest.raises(ValidationError):
            PatientDataSchema(**data)

    def test_rejects_missing_required_email(self) -> None:
        data = _valid_payload()
        del data["email"]
        with pytest.raises(ValidationError):
            PatientDataSchema(**data)

    def test_rejects_invalid_email_format(self) -> None:
        data = _valid_payload()
        data["email"] = "not-an-email"
        with pytest.raises(ValidationError):
            PatientDataSchema(**data)

    def test_rejects_phone_with_letters(self) -> None:
        data = _valid_payload()
        data["phone"] = "555-ABCD-1234"
        with pytest.raises(ValidationError):
            PatientDataSchema(**data)

    def test_rejects_phone_too_short(self) -> None:
        data = _valid_payload()
        data["phone"] = "555123456"
        with pytest.raises(ValidationError):
            PatientDataSchema(**data)

    def test_rejects_phone_too_long(self) -> None:
        data = _valid_payload()
        data["phone"] = "55512345678"
        with pytest.raises(ValidationError):
            PatientDataSchema(**data)

    def test_normalizes_formatted_phone(self) -> None:
        data = _valid_payload()
        data["phone"] = "(555) 123-4567"
        payload = PatientDataSchema(**data)
        assert payload.phone == "5551234567"

    def test_rejects_overlong_reason(self) -> None:
        data = _valid_payload()
        data["reason"] = "x" * 501
        with pytest.raises(ValidationError):
            PatientDataSchema(**data)

    def test_rejects_overlong_name(self) -> None:
        data = _valid_payload()
        data["name"] = "x" * 101
        with pytest.raises(ValidationError):
            PatientDataSchema(**data)

    def test_optional_reason_defaults_to_none(self) -> None:
        data = _valid_payload()
        del data["reason"]
        payload = PatientDataSchema(**data)
        assert payload.reason is None
