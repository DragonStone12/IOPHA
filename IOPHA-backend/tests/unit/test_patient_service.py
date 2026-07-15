import pytest

from app.exceptions import DuplicatePatientError, PatientNotFoundException
from app.repositories.patient_repository import InMemoryPatientRepository
from app.schemas.patient.patient_demographics import PatientIntakeRequest
from app.services.patient_service import InMemoryPatientIntakeService


def _valid_intake() -> PatientIntakeRequest:
    return PatientIntakeRequest.model_validate(
        {
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
    )


class TestPatientIntakeService:
    def test_submit_creates_record_with_generated_id(self) -> None:
        service = InMemoryPatientIntakeService(InMemoryPatientRepository())
        result = service.submit_intake(_valid_intake())
        assert result.patientId.startswith("pat-")
        assert result.firstName == "Jane"
        # SSN must never be echoed to the response.
        assert "ssn" not in result.model_dump()

    def test_duplicate_ssn_raises(self) -> None:
        repo = InMemoryPatientRepository()
        service = InMemoryPatientIntakeService(repo)
        service.submit_intake(_valid_intake())
        with pytest.raises(DuplicatePatientError):
            service.submit_intake(_valid_intake())

    def test_get_demographics_returns_created_record(self) -> None:
        service = InMemoryPatientIntakeService(InMemoryPatientRepository())
        created = service.submit_intake(_valid_intake())
        fetched = service.get_demographics(created.patientId)
        assert fetched.patientId == created.patientId
        assert fetched.email == "jane.doe@example.com"

    def test_get_demographics_missing_raises(self) -> None:
        service = InMemoryPatientIntakeService(InMemoryPatientRepository())
        with pytest.raises(PatientNotFoundException):
            service.get_demographics("pat-does-not-exist")
