from fastapi.testclient import TestClient

from app.dependencies import get_intake_service
from app.exceptions import IntakeProcessingException
from app.main import app
from app.schemas.patient.patient_data import PatientDataSchema
from app.services.intake_service import IntakeService


class MockFailingIntakeService(IntakeService):
    def submit_intake(self, payload: PatientDataSchema) -> dict:
        raise IntakeProcessingException(
            "The intake processing queue failed to ingest the provided "
            "profile information due to constraint rule violations."
        )


class TestPatientIntakeEndpoint:
    def test_intake_happy_path(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/patients/intake",
                json={
                    "name": "Alex Stone",
                    "email": "alex@example.com",
                    "phone": "5551234567",
                    "reason": "Initial Consultation",
                },
            )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "processed"
        assert body["id"] == "pt-1122"

    def test_intake_validation_error_returns_422_problem(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/patients/intake",
                json={
                    "name": "Alex Stone",
                    "email": "not-an-email",
                    "phone": "5551234567",
                },
            )
        assert response.status_code == 422
        body = response.json()
        assert body["status"] == 422
        assert body["title"] == "Unprocessable Content"
        assert "help_url" in body

    def test_intake_fault_injection_returns_422_with_runbook(
        self,
    ) -> None:
        app.dependency_overrides[get_intake_service] = lambda: (
            MockFailingIntakeService()
        )
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/patients/intake",
                    json={
                        "name": "Fault Tester",
                        "email": "error-trigger@example.com",
                        "phone": "5559998888",
                        "reason": "Forced Test State",
                    },
                    headers={"X-Request-ID": "trace-111-intake-err"},
                )
            assert response.status_code == 422
            body = response.json()
            assert body["status"] == 422
            assert body["title"] == "Intake Processing Failure"
            assert "help_url" in body
            assert "intake-processing-error" in body["help_url"]
        finally:
            app.dependency_overrides.pop(get_intake_service, None)
