from fastapi.testclient import TestClient

from app.dependencies import get_booking_service
from app.exceptions.timeslot_exceptions import (
    ProviderNotFoundException,
    ScheduleLockConflictException,
    TimeSlotUnavailableException,
)
from app.main import app
from tests.mocks.booking_service import MockBookingService


class TestBookingEndpointSmoke:
    def test_returns_201_on_valid_payload(self) -> None:
        app.dependency_overrides[get_booking_service] = lambda: MockBookingService()
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/bookings",
                    json={
                        "providerId": "prov-123",
                        "slotId": "2024-01-15-09:00 AM",
                        "patientData": {
                            "name": "Alex Stone",
                            "email": "alex@example.com",
                            "phone": "5551234567",
                            "reason": "Initial Consultation",
                        },
                    },
                )
            assert response.status_code == 201
            body = response.json()
            assert body["bookingId"] == "bk-test-123"
            assert "summary" in body
            summary = body["summary"]
            assert summary["physician"]["id"] == "prov-123"
            assert summary["time"] == "09:00 AM"
            assert summary["date"] == "2024-01-15"
        finally:
            app.dependency_overrides.pop(get_booking_service, None)

    def test_missing_patient_data_returns_422(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/bookings",
                json={
                    "providerId": "prov-123",
                    "slotId": "2024-01-15-09:00 AM",
                },
            )
        assert response.status_code == 422
        body = response.json()
        assert body["title"] == "Unprocessable Content"

    def test_invalid_email_returns_422(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/bookings",
                json={
                    "providerId": "prov-123",
                    "slotId": "2024-01-15-09:00 AM",
                    "patientData": {
                        "name": "Alex Stone",
                        "email": "not-an-email",
                        "phone": "5551234567",
                    },
                },
            )
        assert response.status_code == 422
        body = response.json()
        assert body["title"] == "Unprocessable Content"

    def test_fault_injection_returns_problem_detail(
        self,
    ) -> None:
        app.dependency_overrides[get_booking_service] = lambda: MockBookingService(
            raise_on_create=TimeSlotUnavailableException("2024-01-15-09:00 AM"),
        )
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/bookings",
                    json={
                        "providerId": "prov-123",
                        "slotId": "2024-01-15-09:00 AM",
                        "patientData": {
                            "name": "Fault Tester",
                            "email": "fault@example.com",
                            "phone": "5559998888",
                        },
                    },
                    headers={"X-Request-ID": "123e4567-e89b-12d3-a456-426614174000"},
                )
            assert response.status_code == 409
            body = response.json()
            assert body["status"] == 409
            assert body["title"] == "Time Slot Unavailable"
            assert "help_url" in body
            assert "time-slot-unavailable" in body["help_url"]
            assert (
                response.headers["X-Request-ID"]
                == "123e4567-e89b-12d3-a456-426614174000"
            )
        finally:
            app.dependency_overrides.pop(get_booking_service, None)

    def test_provider_not_found_fault_returns_404(self) -> None:
        app.dependency_overrides[get_booking_service] = lambda: MockBookingService(
            raise_on_create=ProviderNotFoundException("missing"),
        )
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/bookings",
                    json={
                        "providerId": "missing",
                        "slotId": "2024-01-15-09:00 AM",
                        "patientData": {
                            "name": "Fault Tester",
                            "email": "fault@example.com",
                            "phone": "5559998888",
                        },
                    },
                    headers={"X-Request-ID": "123e4567-e89b-12d3-a456-426614174001"},
                )
            assert response.status_code == 404
            body = response.json()
            assert body["status"] == 404
            assert body["title"] == "Provider Not Found"
            assert "provider-not-found-error" in body["help_url"]
        finally:
            app.dependency_overrides.pop(get_booking_service, None)

    def test_schedule_lock_conflict_fault_returns_409(self) -> None:
        app.dependency_overrides[get_booking_service] = lambda: MockBookingService(
            raise_on_create=ScheduleLockConflictException(
                "2024-01-15-09:00 AM", "prov-123"
            ),
        )
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/bookings",
                    json={
                        "providerId": "prov-123",
                        "slotId": "2024-01-15-09:00 AM",
                        "patientData": {
                            "name": "Fault Tester",
                            "email": "fault@example.com",
                            "phone": "5559998888",
                        },
                    },
                    headers={"X-Request-ID": "123e4567-e89b-12d3-a456-426614174002"},
                )
            assert response.status_code == 409
            body = response.json()
            assert body["status"] == 409
            assert body["title"] == "Schedule Lock Conflict"
            assert "schedule-lock-conflict" in body["help_url"]
        finally:
            app.dependency_overrides.pop(get_booking_service, None)
