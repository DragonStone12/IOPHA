import logging
from datetime import date
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_calendar_repository
from app.main import app
from tests.mocks.calendar_service import MockCalendarService


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
def mock_calendar() -> Generator[MockCalendarService, None, None]:
    service = MockCalendarService()
    app.dependency_overrides[get_calendar_repository] = lambda: service
    yield service
    app.dependency_overrides.pop(get_calendar_repository, None)


class TestTimeSlotSuccessPaths:
    def test_returns_200_with_valid_schema(
        self, mock_calendar: MockCalendarService, log_records: list[logging.LogRecord]
    ) -> None:
        query_date = date.today().isoformat()
        with TestClient(app) as client:
            response = client.get(f"/api/providers/prov-123/slots?date={query_date}")
        assert response.status_code == 200
        body = response.json()
        assert "date" in body
        assert "slots" in body
        assert isinstance(body["slots"], list)
        assert len(body["slots"]) > 0
        slot = body["slots"][0]
        assert set(slot.keys()) == {"id", "time", "label", "available"}
        assert slot["id"].endswith(slot["time"])

    def test_response_includes_request_id_header(
        self, mock_calendar: MockCalendarService
    ) -> None:
        query_date = date.today().isoformat()
        request_id = "123e4567-e89b-12d3-a456-426614174000"
        with TestClient(app) as client:
            response = client.get(
                f"/api/providers/prov-123/slots?date={query_date}",
                headers={"X-Request-ID": request_id},
            )
        assert response.headers["X-Request-ID"] == request_id

    def test_logs_contain_request_context(
        self, mock_calendar: MockCalendarService, log_records: list[logging.LogRecord]
    ) -> None:
        query_date = date.today().isoformat()
        with TestClient(app) as client:
            client.get(f"/api/providers/prov-123/slots?date={query_date}")
        record = next((r for r in log_records if r.msg == "request.start"), None)
        assert record is not None
        ctx = record.__dict__["extra_context"]
        assert ctx["method"] == "GET"
        assert ctx["path"] == "/api/providers/prov-123/slots"

    def test_concurrent_requests_isolate_context(
        self, mock_calendar: MockCalendarService
    ) -> None:
        query_date = date.today().isoformat()
        with TestClient(app) as client:
            response1 = client.get(
                f"/api/providers/prov-123/slots?date={query_date}",
                headers={"X-Request-ID": "123e4567-e89b-12d3-a456-426614174000"},
            )
            response2 = client.get(
                f"/api/providers/prov-123/slots?date={query_date}",
                headers={"X-Request-ID": "123e4567-e89b-12d3-a456-426614174001"},
            )
        assert response1.headers["X-Request-ID"] == (
            "123e4567-e89b-12d3-a456-426614174000"
        )
        assert response2.headers["X-Request-ID"] == (
            "123e4567-e89b-12d3-a456-426614174001"
        )
