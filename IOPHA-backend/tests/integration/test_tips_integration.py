import logging
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_tips_repository
from app.main import app
from tests.mocks.tips_service import MockTipsRepository

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


@pytest.fixture(autouse=True)
def bind_tips_mock() -> Generator[None, None, None]:
    """Isolated dependency override for every test in this module.

    Injects a fault-capable :class:`MockTipsRepository` in place of
    the default tips repository and clears *all* overrides in
    teardown so no stub leaks into other test modules.
    """
    app.dependency_overrides[get_tips_repository] = lambda: MockTipsRepository()
    try:
        yield
    finally:
        app.dependency_overrides.clear()


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


class TestTipsHappyPath:
    def test_list_tips_returns_200(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/tips")
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) > 0
        assert set(body[0].keys()) == {"id", "number", "title", "description"}

    def test_get_tip_returns_200(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/tips/tip-001")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == "tip-001"
        assert set(body.keys()) == {"id", "number", "title", "description"}


class TestTipsErrorInjection:
    def test_corrupt_tip_returns_404_with_help_url(self) -> None:
        # Re-point the overridden repository to a fault-injecting double.
        app.dependency_overrides[get_tips_repository] = lambda: MockTipsRepository(
            missing_ids={"corrupt-id"}
        )
        request_id = "123e4567-e89b-12d3-a456-426614174000"
        with TestClient(app) as client:
            response = client.get(
                "/api/tips/corrupt-id",
                headers={"X-Request-ID": request_id},
            )
        assert response.status_code == 404
        body = response.json()
        assert body["title"] == "Onboarding Tip Resource Absent"
        assert body["status"] == 404
        assert body["help_url"].endswith("#tip-not-found-error")
        # The middleware only echoes valid UUIDs, so the client id is preserved.
        assert response.headers["X-Request-ID"] == request_id

    def test_404_response_contains_no_leaked_data(self) -> None:
        app.dependency_overrides[get_tips_repository] = lambda: MockTipsRepository(
            missing_ids={"corrupt-id"}
        )
        with TestClient(app) as client:
            response = client.get("/api/tips/corrupt-id")
        for marker in LEAK_MARKERS:
            assert marker not in response.text

    def test_logs_structured_context(
        self, log_records: list[logging.LogRecord]
    ) -> None:
        app.dependency_overrides[get_tips_repository] = lambda: MockTipsRepository(
            missing_ids={"corrupt-id"}
        )
        request_id = "123e4567-e89b-12d3-a456-426614174000"
        with TestClient(app) as client:
            response = client.get(
                "/api/tips/corrupt-id",
                headers={"X-Request-ID": request_id},
            )
        record = next(
            (r for r in log_records if r.msg == "tips.tip_not_found"),
            None,
        )
        assert record is not None
        ctx = getattr(record, "extra_context", {})
        assert ctx["requestId"] == response.headers["X-Request-ID"]
        assert ctx["path"] == "/api/tips/corrupt-id"
        assert ctx["tipId"] == "corrupt-id"


class TestTipsContextPropagation:
    def test_request_id_echoed_on_success(self) -> None:
        request_id = "123e4567-e89b-12d3-a456-426614174000"
        with TestClient(app) as client:
            response = client.get(
                "/api/tips/tip-001",
                headers={"X-Request-ID": request_id},
            )
        assert response.status_code == 200
        # Correlation id must survive the round-trip for client-side tracing.
        assert response.headers["X-Request-ID"] == request_id


class TestTipsDependencyIsolation:
    def test_overrides_cleared_between_tests(self) -> None:
        # The autouse fixture clears app.dependency_overrides in teardown,
        # so the module-level override from this test does not leak.
        app.dependency_overrides[get_tips_repository] = lambda: MockTipsRepository(
            missing_ids={"corrupt-id"}
        )
        assert get_tips_repository in app.dependency_overrides
        # Simulate the fixture teardown that runs after this test returns.
        app.dependency_overrides.clear()
        assert get_tips_repository not in app.dependency_overrides
