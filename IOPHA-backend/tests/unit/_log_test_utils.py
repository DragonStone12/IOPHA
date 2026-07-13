import json
import logging
from collections.abc import Mapping, Sequence
from typing import Generator

import pytest


class _JsonCaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[dict[str, object]] = []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            parsed = json.loads(self.format(record))
            self.records.append(parsed)
        except (json.JSONDecodeError, Exception):
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


def format_log_record(
    msg: str,
    name: str = "iopha.backend",
    level: int = logging.INFO,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    """Format a synthetic log record and return the parsed JSON payload."""
    from app.core.logging_config import JSONLogFormatter

    rec = logging.LogRecord(
        name=name,
        level=level,
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=None,
    )
    if extra is not None:
        rec.extra_context = extra
    return json.loads(JSONLogFormatter().format(rec))


def assert_no_string_contains(value: object, forbidden: str) -> None:
    """Recursively assert no string value in *value* contains *forbidden*."""
    if isinstance(value, str):
        assert forbidden not in value, f"Leaked '{forbidden}' in {value!r}"
    elif isinstance(value, Mapping):
        for key, val in value.items():
            assert_no_string_contains(key, forbidden)
            assert_no_string_contains(val, forbidden)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        for item in value:
            assert_no_string_contains(item, forbidden)


def assert_any_string_contains(value: object, expected: str) -> None:
    """Recursively assert at least one string value in *value* contains *expected*."""
    found = False

    def _walk(v: object) -> None:
        nonlocal found
        if found:
            return
        if isinstance(v, str):
            if expected in v:
                found = True
        elif isinstance(v, Mapping):
            for val in v.values():
                _walk(val)
        elif isinstance(v, Sequence) and not isinstance(v, (bytes, bytearray)):
            for item in v:
                _walk(item)

    _walk(value)
    assert found, f"Expected substring {expected!r} not found in any string"
