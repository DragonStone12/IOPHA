from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.patient.patient_demographics import (
    AddressRecord,
    EmergencyContactRecord,
    Gender,
    PatientDemographicsSchema,
    PatientIntakeRequest,
    PatientRecord,
    map_record_to_demographics,
)


def _valid_intake() -> dict:
    return {
        "firstName": "Jane",
        "lastName": "Doe",
        "dateOfBirth": "1990-05-14",
        "ssn": "123-45-6789",
        "gender": "Female",
        "address": {
            "street": "123 Main St",
            "city": "Dallas",
            "state": "TX",
            "postalCode": "75201",
            "country": "USA",
        },
        "phoneNumber": "+12145550123",
        "email": "jane.doe@example.com",
        "emergencyContact": {
            "name": "John Doe",
            "relationship": "Spouse",
            "phoneNumber": "+12145550987",
        },
        "preferredCommunication": ["Email", "SMS"],
    }


class TestPatientIntakeRequestValidation:
    def test_accepts_valid_payload(self) -> None:
        payload = PatientIntakeRequest(**_valid_intake())
        assert payload.firstName == "Jane"
        assert payload.dateOfBirth == date(1990, 5, 14)
        assert payload.preferredCommunication == ["Email", "SMS"]

    def test_rejects_unknown_field(self) -> None:
        data = _valid_intake()
        data["unknownField"] = "nope"
        with pytest.raises(ValidationError):
            PatientIntakeRequest(**data)

    def test_rejects_missing_required_field(self) -> None:
        data = _valid_intake()
        del data["ssn"]
        with pytest.raises(ValidationError):
            PatientIntakeRequest(**data)

    def test_rejects_invalid_email(self) -> None:
        data = _valid_intake()
        data["email"] = "not-an-email"
        with pytest.raises(ValidationError):
            PatientIntakeRequest(**data)

    def test_rejects_invalid_phone(self) -> None:
        data = _valid_intake()
        data["phoneNumber"] = "call-me-maybe"
        with pytest.raises(ValidationError):
            PatientIntakeRequest(**data)

    def test_rejects_empty_preferred_communication(self) -> None:
        data = _valid_intake()
        data["preferredCommunication"] = []
        with pytest.raises(ValidationError):
            PatientIntakeRequest(**data)

    def test_rejects_first_name_exceeding_max_length(self) -> None:
        data = _valid_intake()
        data["firstName"] = "A" * 101
        with pytest.raises(ValidationError):
            PatientIntakeRequest(**data)

    def test_accepts_boundary_first_name(self) -> None:
        data = _valid_intake()
        data["firstName"] = "A" * 100
        assert PatientIntakeRequest(**data).firstName == "A" * 100

    def test_rejects_invalid_date_of_birth(self) -> None:
        data = _valid_intake()
        data["dateOfBirth"] = "05/14/1990"
        with pytest.raises(ValidationError):
            PatientIntakeRequest(**data)

    def test_rejects_future_date_of_birth(self) -> None:
        data = _valid_intake()
        data["dateOfBirth"] = "2099-01-01"
        with pytest.raises(ValidationError):
            PatientIntakeRequest(**data)

    def test_accepts_today_as_date_of_birth(self) -> None:
        data = _valid_intake()
        data["dateOfBirth"] = date.today().isoformat()
        assert PatientIntakeRequest(**data).dateOfBirth == date.today()

    def test_rejects_invalid_gender_value(self) -> None:
        data = _valid_intake()
        data["gender"] = "male"  # must match a controlled vocabulary member
        with pytest.raises(ValidationError):
            PatientIntakeRequest(**data)

    def test_accepts_controlled_gender_values(self) -> None:
        for value in ("Female", "Male", "Other", "PreferNotToSay", "Unknown"):
            data = _valid_intake()
            data["gender"] = value
            assert PatientIntakeRequest(**data).gender.value == value

    def test_rejects_unknown_address_field(self) -> None:
        data = _valid_intake()
        data["address"]["floor"] = "3"
        with pytest.raises(ValidationError):
            PatientIntakeRequest(**data)


class TestPatientDemographicsSchema:
    def test_accepts_valid_dto(self) -> None:
        data = _valid_intake()
        # The response DTO deliberately omits the SSN field.
        data.pop("ssn")
        data["patientId"] = "pat-abc123"
        schema = PatientDemographicsSchema(**data)
        assert schema.patientId == "pat-abc123"

    def test_rejects_ssn_in_response_contract(self) -> None:
        # The response DTO must never carry an SSN field, even if a client
        # fabricates one. extra="forbid" rejects it.
        data = _valid_intake()
        data["patientId"] = "pat-abc123"
        data["ssn"] = "123-45-6789"
        with pytest.raises(ValidationError):
            PatientDemographicsSchema(**data)


class TestMapper:
    def test_maps_record_and_drops_ssn(self) -> None:
        record = PatientRecord(
            patient_id="pat-abc123",
            first_name="Jane",
            last_name="Doe",
            date_of_birth=date(1990, 5, 14),
            ssn="123-45-6789",
            gender=Gender("Female"),
            address=AddressRecord("123 Main St", "Dallas", "TX", "75201", "USA"),
            phone_number="+12145550123",
            email="jane.doe@example.com",
            emergency_contact=EmergencyContactRecord(
                "John Doe", "Spouse", "+12145550987"
            ),
            preferred_communication=["Email", "SMS"],
        )
        dto = map_record_to_demographics(record)
        assert dto.patientId == "pat-abc123"
        assert dto.firstName == "Jane"
        assert "ssn" not in dto.model_dump()
        assert dto.address.postalCode == "75201"
        assert dto.emergencyContact.phoneNumber == "+12145550987"
