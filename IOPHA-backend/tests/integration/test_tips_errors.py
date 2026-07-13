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


class TestTipNotFoundException:
    def test_returns_404_with_rfc7807_body(self) -> None:
        mock = MockTipsRepository(missing_ids={"corrupt-id"})
        try:
            app.dependency_overrides[get_tips_repository] = lambda: mock
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
            assert body["instance"] == "/api/tips/corrupt-id"
            assert body["help_url"].endswith("#tip-not-found-error")
            assert body["help_url"].startswith(
                "https://github.com/DragonStone12/IOPHA/blob/main/docs/RUNBOOKS.md#"
            )
            # The middleware only echoes syntactically valid UUIDs, so the
            # client-supplied correlation id is preserved on the response.
            assert response.headers["X-Request-ID"] == request_id
        finally:
            app.dependency_overrides.pop(get_tips_repository, None)

    def test_response_contains_no_leaked_data(self) -> None:
        mock = MockTipsRepository(missing_ids={"corrupt-id"})
        try:
            app.dependency_overrides[get_tips_repository] = lambda: mock
            with TestClient(app) as client:
                response = client.get("/api/tips/corrupt-id")
            for marker in LEAK_MARKERS:
                assert marker not in response.text
        finally:
            app.dependency_overrides.pop(get_tips_repository, None)

    def test_logs_structured_context(
        self, log_records: list[logging.LogRecord]
    ) -> None:
        mock = MockTipsRepository(missing_ids={"corrupt-id"})
        try:
            app.dependency_overrides[get_tips_repository] = lambda: mock
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
            # The handler echoes the same correlation id the middleware
            # assigns and returns on X-Request-ID, so they must agree.
            assert ctx["requestId"] == response.headers["X-Request-ID"]
            assert ctx["path"] == "/api/tips/corrupt-id"
            assert ctx["tipId"] == "corrupt-id"
        finally:
            app.dependency_overrides.pop(get_tips_repository, None)

    def test_valid_tip_returns_200(self) -> None:
        mock = MockTipsRepository()
        try:
            app.dependency_overrides[get_tips_repository] = lambda: mock
            with TestClient(app) as client:
                response = client.get("/api/tips/tip-001")
            assert response.status_code == 200
            body = response.json()
            assert body["id"] == "tip-001"
            assert set(body.keys()) == {"id", "number", "title", "description"}
        finally:
            app.dependency_overrides.pop(get_tips_repository, None)
