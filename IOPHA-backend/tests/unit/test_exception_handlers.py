import logging
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.exceptions import (
    DOMAIN_EXCEPTIONS,
    AttachmentPayloadTooLargeError,
    AvailabilityDriftError,
    ExpiredBookingSessionError,
    ExternalCalendarSyncDisconnectedError,
    IntakeProcessingException,
    InvalidViewTransitionError,
    IOPHADomainError,
    NotificationGatewayTimeoutError,
    NutritionEvaluationEngineError,
    OutOfOrderMessageDeliveryError,
    OverlappingModifierConflictError,
    ProviderNotFoundException,
    RaceConditionDoubleBookingError,
    SearchAggregatorTimeoutError,
    TimeZoneMismatchError,
    TipNotFoundException,
    UnreadNotificationInconsistencyError,
    UpstreamWebhookFailureError,
    WebSocketConnectionDropError,
)
from app.utils.handlers import register_exception_handlers

# Substrings that must NEVER appear in a client-facing error response.
LEAK_MARKERS = (
    "Traceback",
    "Exception(",
    "0x",
    "password",
    "secret",
    "Bearer ",
    "postgresql",
)

EXAMPLES: dict[str, IOPHADomainError] = {
    "race": RaceConditionDoubleBookingError("slot-1", "pat-1"),
    "tz": TimeZoneMismatchError("slot-2", "pat-2"),
    "drift": AvailabilityDriftError("slot-3", "pat-3"),
    "overlap": OverlappingModifierConflictError("slot-4", "pat-4", "slot-4b"),
    "ws": WebSocketConnectionDropError("sess-5", "pat-5"),
    "ooo": OutOfOrderMessageDeliveryError("sess-6", "msg-6", 1, 2),
    "unread": UnreadNotificationInconsistencyError("sess-7", "pat-7", "msg-7"),
    "attach": AttachmentPayloadTooLargeError("sess-8", "pat-8", 5_000_000, 9_000_000),
    "cal": ExternalCalendarSyncDisconnectedError("prov-9", "pat-9"),
    "webhook": UpstreamWebhookFailureError("appt-10", "pat-10", "ehr.example.com"),
    "notif": NotificationGatewayTimeoutError("pat-11", "sms"),
    "view": InvalidViewTransitionError("confirmation", "time-selection", "prov-12"),
    "expired": ExpiredBookingSessionError("slot-13", "pat-13", 600),
    "search": SearchAggregatorTimeoutError("Cardiologist near 10001"),
    "provider": ProviderNotFoundException("prov-1"),
    "tip": TipNotFoundException("tip-1"),
    "nutrition": NutritionEvaluationEngineError("corrupt-profile"),
    "intake": IntakeProcessingException("constraint violation"),
}


class _CaptureHandler(logging.Handler):
    def __init__(self, sink: list[logging.LogRecord]) -> None:
        super().__init__()
        self._sink = sink

    def emit(self, record: logging.LogRecord) -> None:
        self._sink.append(record)


def _make_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/errors/{key}")
    async def trigger(key: str) -> dict[str, str]:
        if key == "unexpected":
            raise RuntimeError("simulated unhandled fault")
        if key not in EXAMPLES:
            raise ValueError(f"unknown key: {key}")
        raise EXAMPLES[key]

    @app.get("/validate")
    async def validate(q: int) -> dict[str, int]:
        return {"q": q}

    @app.post("/intake")
    async def intake() -> dict[str, str]:
        raise IntakeProcessingException("constraint violation")

    return app


@pytest.fixture
def client() -> TestClient:
    # The global Exception handler is wired into Starlette's
    # ServerErrorMiddleware, which re-raises the original exception after
    # building the response. Disabling raise_server_exceptions lets the test
    # assert on the returned 500 payload instead of the re-raised error.
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


def _find_record(
    records: list[logging.LogRecord], event: str
) -> logging.LogRecord | None:
    for rec in records:
        if rec.msg == event:
            return rec
    return None


def _context(rec: logging.LogRecord) -> dict[str, Any]:
    return rec.__dict__["extra_context"]


class TestDomainExceptionHandlers:
    @pytest.mark.parametrize("key", list(EXAMPLES.keys()))
    def test_returns_structured_payload(self, client: TestClient, key: str) -> None:
        exc = EXAMPLES[key]
        response = client.get(f"/errors/{key}")
        assert response.status_code == exc.status_code
        body = response.json()
        assert body["title"] == exc.title
        assert body["status"] == exc.status_code
        assert body["instance"] == f"/errors/{key}"
        assert body["help_url"].endswith(f"#{exc.link}")
        assert body["help_url"].startswith(
            "https://github.com/DragonStone12/IOPHA/blob/main/docs/RUNBOOKS.md#"
        )

    @pytest.mark.parametrize("key", list(EXAMPLES.keys()))
    def test_payload_contains_no_leaked_data(
        self, client: TestClient, key: str
    ) -> None:
        response = client.get(f"/errors/{key}")
        for marker in LEAK_MARKERS:
            assert marker not in response.text

    @pytest.mark.parametrize("key", list(EXAMPLES.keys()))
    def test_logs_structured_context(
        self, client: TestClient, log_records: list[logging.LogRecord], key: str
    ) -> None:
        exc = EXAMPLES[key]
        client.get(f"/errors/{key}")
        record = _find_record(log_records, exc.log_event)
        assert record is not None
        ctx = _context(record)
        assert ctx["requestId"] == "unknown"
        assert ctx["path"] == f"/errors/{key}"


class TestGlobalExceptionHandler:
    def test_returns_500_with_generic_detail(self, client: TestClient) -> None:
        response = client.get("/errors/unexpected")
        assert response.status_code == 500
        body = response.json()
        assert body["title"] == "Internal Server Error"
        assert body["status"] == 500
        assert (
            body["detail"] == "An unexpected server-side process interruption occurred."
        )
        assert body["help_url"].endswith("#internal-server-error")

    def test_generic_detail_has_no_leaked_data(self, client: TestClient) -> None:
        response = client.get("/errors/unexpected")
        for marker in LEAK_MARKERS:
            assert marker not in response.text

    def test_captures_trace_server_side_only(
        self, client: TestClient, log_records: list[logging.LogRecord]
    ) -> None:
        client.get("/errors/unexpected")
        record = _find_record(log_records, "request.unexpected_error")
        assert record is not None
        assert record.exc_info is not None
        ctx = _context(record)
        assert "userAgent" in ctx
        assert ctx["path"] == "/errors/unexpected"


class TestHeaderDegradation:
    def test_request_id_defaults_to_unknown(
        self, client: TestClient, log_records: list[logging.LogRecord]
    ) -> None:
        client.get("/errors/race")
        record = _find_record(log_records, EXAMPLES["race"].log_event)
        assert record is not None
        assert _context(record)["requestId"] == "unknown"

    def test_request_id_propagated_when_present(
        self, client: TestClient, log_records: list[logging.LogRecord]
    ) -> None:
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        client.get("/errors/race", headers={"X-Request-ID": valid_uuid})
        record = _find_record(log_records, EXAMPLES["race"].log_event)
        assert record is not None
        assert _context(record)["requestId"] == valid_uuid


class TestRoutingRegistry:
    def test_every_domain_exception_is_registered(self) -> None:
        assert RaceConditionDoubleBookingError in DOMAIN_EXCEPTIONS
        assert AttachmentPayloadTooLargeError in DOMAIN_EXCEPTIONS
        assert InvalidViewTransitionError in DOMAIN_EXCEPTIONS
        assert SearchAggregatorTimeoutError in DOMAIN_EXCEPTIONS
        assert len(DOMAIN_EXCEPTIONS) == len(EXAMPLES)


class TestValidationErrorHandler:
    def test_validation_error_returns_problem_with_help_url(
        self, client: TestClient
    ) -> None:
        response = client.get("/validate?q=not-an-int")
        assert response.status_code == 422
        body = response.json()
        assert body["status"] == 422
        assert body["title"] == "Unprocessable Entity"
        assert "help_url" in body
        assert "unprocessable-entity-error" in body["help_url"]
        assert body["errors"] is not None
        # Raw user input must never leak into the response body.
        assert "not-an-int" not in response.text
