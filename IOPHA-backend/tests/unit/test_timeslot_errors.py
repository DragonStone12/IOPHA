import logging
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.exceptions.error_handlers import register_timeslot_error_handlers
from app.exceptions.timeslot_exceptions import (
    AppBaseException,
    InvalidTimeSlotFormatException,
    ProviderNotFoundException,
    TimeSlotUnavailableException,
)


class _CaptureHandler(logging.Handler):
    def __init__(self, sink: list[logging.LogRecord]) -> None:
        super().__init__()
        self._sink = sink

    def emit(self, record: logging.LogRecord) -> None:
        self._sink.append(record)


def _make_app() -> FastAPI:
    app = FastAPI()
    register_timeslot_error_handlers(app)

    @app.get("/slots/{slot_id}")
    async def slot_detail(slot_id: str) -> dict[str, str]:
        raise TimeSlotUnavailableException(slot_id)

    @app.get("/providers/{provider_id}")
    async def provider_detail(provider_id: str) -> dict[str, str]:
        raise ProviderNotFoundException(provider_id)

    @app.get("/format")
    async def format_check(details: str = "bad format") -> dict[str, str]:
        raise InvalidTimeSlotFormatException(details)

    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(_make_app(), raise_server_exceptions=False)


@pytest.fixture
def log_records() -> Any:
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
    def test_returns_409_with_rfc7807_body(self, client: TestClient) -> None:
        response = client.get("/slots/2024-01-15-09:00 AM")
        assert response.status_code == 409
        body = response.json()
        assert body["title"] == "Time Slot Unavailable"
        assert body["status"] == 409
        assert body["instance"] == "/slots/2024-01-15-09:00 AM"
        assert body["help_url"].endswith("#time-slot-unavailable")
        assert body["help_url"].startswith(
            "https://github.com/DragonStone12/IOPHA/blob/main/docs/RUNBOOKS.md#"
        )
        assert body["type"] == "about:blank"
        assert body["requestId"] is not None
        assert "2024-01-15-09:00 AM" in body["detail"]

    def test_response_contains_no_leaked_data(self, client: TestClient) -> None:
        response = client.get("/slots/2024-01-15-09:00 AM")
        for marker in ("Traceback", "Exception(", "0x"):
            assert marker not in response.text

    def test_logs_structured_context(
        self, client: TestClient, log_records: list[logging.LogRecord]
    ) -> None:
        client.get("/slots/slot-123")
        record = next((r for r in log_records if r.msg == "timeslot.unavailable"), None)
        assert record is not None
        ctx = getattr(record, "extra_context", {})
        assert ctx["requestId"] == "system"
        assert ctx["path"] == "/slots/slot-123"
        assert ctx["slotId"] == "slot-123"


class TestProviderNotFoundException:
    def test_returns_404_with_rfc7807_body(self, client: TestClient) -> None:
        response = client.get("/providers/ghost-provider")
        assert response.status_code == 404
        body = response.json()
        assert body["title"] == "Provider Not Found"
        assert body["status"] == 404
        assert body["instance"] == "/providers/ghost-provider"
        assert body["help_url"].endswith("#provider-not-found-error")
        assert body["type"] == "about:blank"
        assert body["requestId"] is not None
        assert "ghost-provider" in body["detail"]

    def test_response_contains_no_leaked_data(self, client: TestClient) -> None:
        response = client.get("/providers/ghost-provider")
        for marker in ("Traceback", "Exception(", "0x"):
            assert marker not in response.text


class TestInvalidTimeSlotFormatException:
    def test_returns_400_with_rfc7807_body(self, client: TestClient) -> None:
        response = client.get("/format?details=time-only")
        assert response.status_code == 400
        body = response.json()
        assert body["title"] == "Invalid Time Slot Format"
        assert body["status"] == 400
        assert body["instance"] == "/format"
        assert body["help_url"].endswith("#invalid-time-slot-format")
        assert body["type"] == "about:blank"
        assert body["requestId"] is not None
        assert "time-only" in body["detail"]

    def test_response_contains_no_leaked_data(self, client: TestClient) -> None:
        response = client.get("/format?details=x")
        for marker in ("Traceback", "Exception(", "0x"):
            assert marker not in response.text


class TestAppBaseException:
    def test_is_iopha_domain_error(self) -> None:
        exc = TimeSlotUnavailableException("slot-1")
        assert isinstance(exc, AppBaseException)
        assert isinstance(exc, Exception)
