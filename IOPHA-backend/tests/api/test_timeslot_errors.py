import logging
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_calendar_repository
from app.main import app
from tests.mocks.calendar_service import MockCalendarService

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
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        yield records
    finally:
        logger.removeHandler(handler)


@pytest.fixture
def log_sink() -> Generator[list[logging.LogRecord], None, None]:
    records: list[logging.LogRecord] = []
    handler = _CaptureHandler(records)
    logger = logging.getLogger("iopha.backend")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        yield records
    finally:
        logger.removeHandler(handler)


class TestTimeSlotUnavailableException:
    def test_returns_409_with_rfc7807_body(self) -> None:
        mock = MockCalendarService(reserve_succeeds=False)
        app.dependency_overrides[get_calendar_repository] = lambda: mock
        try:
            request_id = "123e4567-e89b-12d3-a456-426614174000"
            with TestClient(app) as client:
                response = client.post(
                    "/api/providers/prov-123/slots/2024-01-15-09%3A00%20AM/reserve",
                    headers={"X-Request-ID": request_id},
                )
            assert response.status_code == 409
            body = response.json()
            assert body["title"] == "Time Slot Unavailable"
            assert body["status"] == 409
            assert (
                body["instance"]
                == "/api/providers/prov-123/slots/2024-01-15-09:00 AM/reserve"
            )
            assert body["help_url"].endswith("#time-slot-unavailable")
            assert body["type"] == "about:blank"
            assert response.headers["X-Request-ID"] == request_id
        finally:
            app.dependency_overrides.pop(get_calendar_repository, None)

    def test_response_contains_no_leaked_data(self) -> None:
        mock = MockCalendarService(reserve_succeeds=False)
        app.dependency_overrides[get_calendar_repository] = lambda: mock
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/providers/prov-123/slots/2024-01-15-09%3A00%20AM/reserve",
                )
            for marker in LEAK_MARKERS:
                assert marker not in response.text
        finally:
            app.dependency_overrides.pop(get_calendar_repository, None)

    def test_logs_structured_context(
        self, log_records: list[logging.LogRecord]
    ) -> None:
        mock = MockCalendarService(reserve_succeeds=False)
        app.dependency_overrides[get_calendar_repository] = lambda: mock
        try:
            with TestClient(app) as client:
                client.post(
                    "/api/providers/prov-123/slots/2024-01-15-09%3A00%20AM/reserve"
                )
            record = next(
                (r for r in log_records if r.msg == "timeslot.unavailable"), None
            )
            assert record is not None
            ctx = record.__dict__["extra_context"]
            assert ctx["requestId"] == "unknown"
            assert (
                ctx["path"]
                == "/api/providers/prov-123/slots/2024-01-15-09:00 AM/reserve"
            )
            assert ctx["slotId"] == "2024-01-15-09:00 AM"
        finally:
            app.dependency_overrides.pop(get_calendar_repository, None)


class TestProviderNotFoundException:
    def test_returns_404_with_help_url(self) -> None:
        mock = MockCalendarService()
        app.dependency_overrides[get_calendar_repository] = lambda: mock
        try:
            request_id = "123e4567-e89b-12d3-a456-426614174000"
            with TestClient(app) as client:
                response = client.get(
                    "/api/providers/does-not-exist/slots",
                    headers={"X-Request-ID": request_id},
                )
            assert response.status_code == 404
            body = response.json()
            assert body["title"] == "Provider Not Found"
            assert body["status"] == 404
            assert body["help_url"].endswith("#provider-not-found-error")
            assert response.headers["X-Request-ID"] == request_id
        finally:
            app.dependency_overrides.pop(get_calendar_repository, None)

    def test_response_contains_no_leaked_data(self) -> None:
        mock = MockCalendarService()
        app.dependency_overrides[get_calendar_repository] = lambda: mock
        try:
            with TestClient(app) as client:
                response = client.get("/api/providers/does-not-exist/slots")
            for marker in LEAK_MARKERS:
                assert marker not in response.text
        finally:
            app.dependency_overrides.pop(get_calendar_repository, None)


class TestInvalidTimeSlotFormatException:
    def test_returns_400_with_validation_details(self) -> None:
        mock = MockCalendarService()
        app.dependency_overrides[get_calendar_repository] = lambda: mock
        try:
            request_id = "123e4567-e89b-12d3-a456-426614174000"
            with TestClient(app) as client:
                response = client.post(
                    "/api/providers/prov-123/slots/bad-format/reserve",
                    headers={"X-Request-ID": request_id},
                )
            assert response.status_code == 400
            body = response.json()
            assert body["title"] == "Invalid Time Slot Format"
            assert body["status"] == 400
            assert body["help_url"].endswith("#invalid-time-slot-format")
            assert response.headers["X-Request-ID"] == request_id
        finally:
            app.dependency_overrides.pop(get_calendar_repository, None)

    def test_response_contains_no_leaked_data(self) -> None:
        mock = MockCalendarService()
        app.dependency_overrides[get_calendar_repository] = lambda: mock
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/providers/prov-123/slots/bad-format/reserve"
                )
            for marker in LEAK_MARKERS:
                assert marker not in response.text
        finally:
            app.dependency_overrides.pop(get_calendar_repository, None)
