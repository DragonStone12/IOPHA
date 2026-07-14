import json
import logging
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class _JsonCaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[dict[str, object]] = []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            parsed = json.loads(self.format(record))
            self.records.append(parsed)
        except Exception:
            self.handleError(record)


@pytest.fixture
def json_log_records() -> Generator[list[dict[str, object]], None, None]:
    from app.core.logging_config import JSONLogFormatter

    logger = logging.getLogger("iopha.backend")
    original_level = logger.level
    handler = _JsonCaptureHandler()
    handler.setFormatter(JSONLogFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        yield handler.records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(original_level)
