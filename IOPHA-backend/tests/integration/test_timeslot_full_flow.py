import logging
from collections.abc import Generator
from typing import Any

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


def _apply_mock(mock: MockCalendarService) -> None:
    app.dependency_overrides[get_calendar_repository] = lambda: mock


def _clear_mock() -> None:
    app.dependency_overrides.pop(get_calendar_repository, None)


def _assert_no_leaks(text: str) -> None:
    for marker in LEAK_MARKERS:
        assert marker not in text, f"Leak marker '{marker}' found in response"


def _assert_problem_detail(
    body: dict[str, Any],
    status: int,
    title: str,
    link: str,
) -> None:
    assert body["status"] == status
    assert body["title"] == title
    assert "type" not in body
    assert body["help_url"].endswith(f"#{link}")
    assert body["instance"].startswith("/api/providers/")


def _logged_messages(records: list[logging.LogRecord]) -> list[str]:
    return [r.getMessage() for r in records]


class TestTimeSlotFullRequestFlow:
    def test_get_slots_full_lifecycle(
        self, log_records: list[logging.LogRecord]
    ) -> None:
        mock = MockCalendarService()
        _apply_mock(mock)
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get(
                    "/api/providers/prov-123/slots",
                    headers={"X-Request-ID": "123e4567-e89b-12d3-a456-426614174000"},
                )
        finally:
            _clear_mock()

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list) and len(body) > 0
        slot = body[0]
        assert set(slot.keys()) == {"id", "time", "label", "available"}
        assert (
            response.headers["X-Request-ID"] == "123e4567-e89b-12d3-a456-426614174000"
        )

        messages = _logged_messages(log_records)
        assert "request.start" in messages
        assert "request.complete" in messages

        start = next(r for r in log_records if r.msg == "request.start")
        complete = next(r for r in log_records if r.msg == "request.complete")
        assert getattr(start, "extra_context", {})["method"] == "GET"
        assert (
            getattr(start, "extra_context", {})["path"]
            == "/api/providers/prov-123/slots"
        )
        assert getattr(complete, "extra_context", {})["status"] == 200
        complete_ctx = getattr(complete, "extra_context", {})
        assert "durationMs" in complete_ctx
        assert complete_ctx["responseSize"] >= 0

        _assert_no_leaks(response.text)

    def test_post_reserve_success_body_shape(self) -> None:
        mock = MockCalendarService()
        slot_id = mock.first_slot_id
        _apply_mock(mock)
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    f"/api/providers/prov-123/slots/{slot_id}/reserve",
                    headers={"X-Request-ID": "123e4567-e89b-12d3-a456-426614174001"},
                )
        finally:
            _clear_mock()

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "reserved"
        assert body["slot_id"] == slot_id
        assert (
            response.headers["X-Request-ID"] == "123e4567-e89b-12d3-a456-426614174001"
        )

    def test_error_flows_trigger_correct_handlers(
        self, log_records: list[logging.LogRecord]
    ) -> None:
        cases = [
            (
                MockCalendarService(reserve_succeeds=False),
                "post",
                "/api/providers/prov-123/slots/2024-01-15-09:00 AM/reserve",
                409,
                "Time Slot Unavailable",
                "time-slot-unavailable",
                "timeslot.unavailable",
                "2024-01-15-09:00 AM",
            ),
            (
                MockCalendarService(),
                "get",
                "/api/providers/does-not-exist/slots",
                404,
                "Provider Not Found",
                "provider-not-found-error",
                "directory.provider_not_found",
                "does-not-exist",
            ),
            (
                MockCalendarService(),
                "post",
                "/api/providers/prov-123/slots/bad-format/reserve",
                400,
                "Invalid Time Slot Format",
                "invalid-time-slot-format",
                "timeslot.invalid_format",
                None,
            ),
        ]

        request_ids = [
            "123e4567-e89b-12d3-a456-426614174010",
            "123e4567-e89b-12d3-a456-426614174011",
            "123e4567-e89b-12d3-a456-426614174012",
        ]

        for idx, case in enumerate(cases):
            (
                mock,
                method,
                path,
                status,
                title,
                link,
                expected_log_event,
                expected_slot_or_provider_id,
            ) = case
            request_id = request_ids[idx]
            _apply_mock(mock)
            try:
                with TestClient(app, raise_server_exceptions=False) as client:
                    if method == "get":
                        resp = client.get(path, headers={"X-Request-ID": request_id})
                    else:
                        resp = client.post(path, headers={"X-Request-ID": request_id})
            finally:
                _clear_mock()

            assert resp.status_code == status, f"Expected {status} for {path}"
            body = resp.json()
            _assert_problem_detail(body, status, title, link)
            assert body["requestId"] == request_id
            _assert_no_leaks(resp.text)

            record = next((r for r in log_records if r.msg == expected_log_event), None)
            assert record is not None, f"Missing log event {expected_log_event}"
            ctx = getattr(record, "extra_context", {})
            assert ctx["requestId"] == request_id
            assert ctx["path"] == path
            if expected_slot_or_provider_id is not None:
                if link == "time-slot-unavailable":
                    assert ctx["slotId"] == expected_slot_or_provider_id
                else:
                    assert ctx["providerId"] == expected_slot_or_provider_id

            log_records.clear()

    def test_raise_server_exceptions_false_returns_rfc7807(
        self, log_records: list[logging.LogRecord]
    ) -> None:
        mock = MockCalendarService(reserve_succeeds=False)
        _apply_mock(mock)
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/providers/prov-123/slots/2024-01-15-09:00 AM/reserve",
                )
        finally:
            _clear_mock()

        assert response.status_code == 409
        body = response.json()
        assert "type" not in body
        assert body["status"] == 409
        assert body["help_url"].endswith("#time-slot-unavailable")
        assert response.headers.get("X-Request-ID") is not None
        _assert_no_leaks(response.text)

    def test_request_id_persists_through_all_layers(self) -> None:
        mock = MockCalendarService()
        _apply_mock(mock)
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get(
                    "/api/providers/prov-123/slots",
                    headers={"X-Request-ID": "123e4567-e89b-12d3-a456-426614174002"},
                )
        finally:
            _clear_mock()

        assert (
            response.headers["X-Request-ID"] == "123e4567-e89b-12d3-a456-426614174002"
        )
        body = response.json()
        assert isinstance(body, list)
        assert len(body) > 0

    def test_no_dependency_override_leak_between_tests(self) -> None:
        assert get_calendar_repository not in app.dependency_overrides

    def test_openapi_contract_rewrites_422_to_problem_detail(self) -> None:
        spec = app.openapi()
        provider_path = spec["paths"]["/api/providers/{provider_id}"]
        get_op = provider_path["get"]
        assert "404" in get_op["responses"]
        assert "422" in get_op["responses"]
        ref = get_op["responses"]["422"]["content"]["application/json"]["schema"]
        assert ref["$ref"].endswith("ProblemDetail")
