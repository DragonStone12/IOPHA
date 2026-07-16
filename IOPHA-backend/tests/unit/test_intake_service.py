from app.schemas.patient.patient_data import PatientDataSchema
from app.services.intake_service import InMemoryIntakeService


class TestInMemoryIntakeService:
    def test_submit_intake_returns_processed_status(self) -> None:
        service = InMemoryIntakeService()
        payload = PatientDataSchema(name="A", email="a@b.com", phone="5551234567")
        result = service.submit_intake(payload)
        assert result == {"status": "processed", "id": "pt-1122"}
