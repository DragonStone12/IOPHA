import logging
from collections.abc import Generator
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.dependencies import (
    get_booking_repository,
    get_booking_service,
    get_calendar_repository,
    get_provider_repository,
)
from app.main import app
from app.repositories.booking_repository import InMemoryBookingRepository
from app.repositories.calendar_repository import InMemoryCalendarRepository
from app.repositories.provider_repository import InMemoryProviderRepository
from app.services.booking_service import InMemoryBookingService

LEAK_MARKERS = (
    "Traceback",
    "Exception(",
    "0x",
    "password",
    "secret",
    "Bearer ",
    "postgresql",
)


class _CaptureHandler(logging.Handler):
    def __init__(self, sink: list[logging.LogRecord]) -> None:
        super().__init__()
        self._sink = sink

    def emit(self, record: logging.LogRecord) -> None:
        self._sink.append(record)


@pytest.fixture
def log_records() -> Generator[list[logging.LogRecord], None, None]:
    records: list[logging.LogRecord] = []
    handler = _CaptureHandler(records)
    logger = logging.getLogger("iopha.backend")
    previous_level = logger.level
    previous_propagate = logger.propagate
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    try:
        yield records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)
        logger.propagate = previous_propagate


def _assert_no_leaks(text: str) -> None:
    for marker in LEAK_MARKERS:
        assert marker not in text, f"Leak marker '{marker}' found in response"


def _assert_problem_detail(
    body: dict[str, Any], status: int, title: str, link: str
) -> None:
    assert body["status"] == status
    assert body["title"] == title
    assert body["help_url"].endswith(f"#{link}")
    assert body["instance"] == "/api/bookings"


class TestBookingFullRequestFlow:
    def test_post_booking_full_lifecycle(
        self, log_records: list[logging.LogRecord]
    ) -> None:
        app.dependency_overrides[get_calendar_repository] = lambda: (
            InMemoryCalendarRepository()
        )
        app.dependency_overrides[get_provider_repository] = lambda: (
            InMemoryProviderRepository()
        )
        app.dependency_overrides[get_booking_repository] = lambda: (
            InMemoryBookingRepository()
        )
        try:
            calendar_repo = InMemoryCalendarRepository()
            slots = calendar_repo.get_slots("prov-123")
            available_slot = next(slot for slot in slots if slot.available)

            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/bookings",
                    json={
                        "providerId": "prov-123",
                        "slotId": available_slot.id,
                        "patientData": {
                            "name": "Alex Stone",
                            "email": "alex@example.com",
                            "phone": "5551234567",
                            "reason": "Initial Consultation",
                        },
                    },
                    headers={"X-Request-ID": "123e4567-e89b-12d3-a456-426614174000"},
                )
        finally:
            app.dependency_overrides.pop(get_calendar_repository, None)
            app.dependency_overrides.pop(get_provider_repository, None)
            app.dependency_overrides.pop(get_booking_repository, None)

        assert response.status_code == 201
        body = response.json()
        assert body["bookingId"].startswith("bk-")
        assert body["summary"]["physician"]["id"] == "prov-123"
        assert body["summary"]["time"] == available_slot.time
        assert body["summary"]["date"] == date.today().isoformat()
        assert (
            response.headers["X-Request-ID"] == "123e4567-e89b-12d3-a456-426614174000"
        )

        messages = [r.getMessage() for r in log_records]
        assert "request.start" in messages
        assert "request.complete" in messages
        assert "booking.created" in messages

        booking_record = next(r for r in log_records if r.msg == "booking.created")
        ctx = getattr(booking_record, "extra_context", {})
        assert ctx["providerId"] == "prov-123"
        assert ctx["slotId"] == available_slot.id
        assert ctx["bookingId"] == body["bookingId"]
        # Patient PII must never appear in logs.
        assert "Alex Stone" not in str(log_records)
        assert "alex@example.com" not in str(log_records)
        assert "5551234567" not in str(log_records)

        _assert_no_leaks(response.text)

    def test_double_booking_returns_409_unavailable(
        self, log_records: list[logging.LogRecord]
    ) -> None:
        # Share repository instances across requests so the first reservation
        # is visible to the second request.
        shared_calendar = InMemoryCalendarRepository()
        shared_booking = InMemoryBookingRepository()
        shared_service = InMemoryBookingService(
            calendar_repository=shared_calendar,
            provider_repository=InMemoryProviderRepository(),
            booking_repository=shared_booking,
        )
        app.dependency_overrides[get_booking_service] = lambda: shared_service
        try:
            slots = shared_calendar.get_slots("prov-123")
            available_slot = next(slot for slot in slots if slot.available)
            payload = {
                "providerId": "prov-123",
                "slotId": available_slot.id,
                "patientData": {
                    "name": "Alex Stone",
                    "email": "alex@example.com",
                    "phone": "5551234567",
                },
            }

            with TestClient(app, raise_server_exceptions=False) as client:
                first = client.post("/api/bookings", json=payload)
                second = client.post("/api/bookings", json=payload)
        finally:
            app.dependency_overrides.pop(get_booking_service, None)

        assert first.status_code == 201
        assert second.status_code == 409
        body = second.json()
        _assert_problem_detail(
            body, 409, "Time Slot Unavailable", "time-slot-unavailable"
        )
        assert body["requestId"] is not None

        log_records.clear()

    def test_unknown_provider_returns_404(self) -> None:
        app.dependency_overrides[get_calendar_repository] = lambda: (
            InMemoryCalendarRepository()
        )
        app.dependency_overrides[get_provider_repository] = lambda: (
            InMemoryProviderRepository()
        )
        app.dependency_overrides[get_booking_repository] = lambda: (
            InMemoryBookingRepository()
        )
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/bookings",
                    json={
                        "providerId": "missing",
                        "slotId": f"{date.today().isoformat()}-09:00 AM",
                        "patientData": {
                            "name": "Alex Stone",
                            "email": "alex@example.com",
                            "phone": "5551234567",
                        },
                    },
                )
        finally:
            app.dependency_overrides.pop(get_calendar_repository, None)
            app.dependency_overrides.pop(get_provider_repository, None)
            app.dependency_overrides.pop(get_booking_repository, None)

        assert response.status_code == 404
        body = response.json()
        _assert_problem_detail(
            body, 404, "Provider Not Found", "provider-not-found-error"
        )

    def test_invalid_slot_format_returns_400(self) -> None:
        app.dependency_overrides[get_calendar_repository] = lambda: (
            InMemoryCalendarRepository()
        )
        app.dependency_overrides[get_provider_repository] = lambda: (
            InMemoryProviderRepository()
        )
        app.dependency_overrides[get_booking_repository] = lambda: (
            InMemoryBookingRepository()
        )
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/bookings",
                    json={
                        "providerId": "prov-123",
                        "slotId": "bad-format",
                        "patientData": {
                            "name": "Alex Stone",
                            "email": "alex@example.com",
                            "phone": "5551234567",
                        },
                    },
                )
        finally:
            app.dependency_overrides.pop(get_calendar_repository, None)
            app.dependency_overrides.pop(get_provider_repository, None)
            app.dependency_overrides.pop(get_booking_repository, None)

        assert response.status_code == 400
        body = response.json()
        _assert_problem_detail(
            body, 400, "Invalid Time Slot Format", "invalid-time-slot-format"
        )

    def test_no_dependency_override_leak_between_tests(self) -> None:
        assert get_calendar_repository not in app.dependency_overrides
        assert get_provider_repository not in app.dependency_overrides
        assert get_booking_repository not in app.dependency_overrides
