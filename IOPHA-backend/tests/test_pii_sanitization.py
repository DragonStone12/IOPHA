import logging

from app.main import (
    PIISanitizerFilter,
)

# ---------------------------------------------------------------------------
# PIISanitizerFilter tests
# ---------------------------------------------------------------------------


class TestPIISanitizerFilter:
    def test_scrubs_email_in_message(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Contact admin@example.com for help",
            args=(),
            exc_info=None,
        )
        assert filt.filter(record) is True
        assert "[EMAIL_REDACTED]" in record.msg
        assert "admin@example.com" not in record.msg

    def test_scrubs_phone_in_message(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Call 555-123-4567 now",
            args=(),
            exc_info=None,
        )
        assert filt.filter(record) is True
        assert "[PHONE_REDACTED]" in record.msg

    def test_scrubs_ssn_in_message(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="SSN: 123-45-6789",
            args=(),
            exc_info=None,
        )
        assert filt.filter(record) is True
        assert "[SSN_REDACTED]" in record.msg

    def test_scrubs_tuple_args(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User %s logged in",
            args=("admin@example.com",),
            exc_info=None,
        )
        assert filt.filter(record) is True
        sanitized = record.msg % record.args
        assert "[EMAIL_REDACTED]" in sanitized
        assert "admin@example.com" not in sanitized

    def test_scrubs_dict_args(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User %(email)s logged in",
            args={"email": "admin@example.com", "id": 1},
            exc_info=None,
        )
        assert filt.filter(record) is True
        sanitized = record.msg % record.args
        assert "[EMAIL_REDACTED]" in sanitized
        assert "admin@example.com" not in sanitized

    def test_scrubs_extra_dict(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Request processed",
            args=(),
            exc_info=None,
        )
        # Python logging merges `extra` kwargs into record.__dict__, not record.extra.
        # Setting record.extra directly would test a code path that never executes.
        record.__dict__["email"] = "admin@example.com"
        record.__dict__["phone"] = "555-123-4567"
        assert filt.filter(record) is True
        assert record.__dict__["email"] == "[EMAIL_REDACTED]"
        assert record.__dict__["phone"] == "[PHONE_REDACTED]"

    def test_non_string_args_untouched(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Count %d",
            args=(42,),
            exc_info=None,
        )
        assert filt.filter(record) is True
        assert record.args == (42,)

    def test_multiple_pii_types_in_message(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Contact admin@example.com or 555-123-4567, SSN: 123-45-6789",
            args=(),
            exc_info=None,
        )
        assert filt.filter(record) is True
        assert "[EMAIL_REDACTED]" in record.msg
        assert "[PHONE_REDACTED]" in record.msg
        assert "[SSN_REDACTED]" in record.msg

    def test_scrubs_credit_card_in_message(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Card: 4111-1111-1111-1111",
            args=(),
            exc_info=None,
        )
        assert filt.filter(record) is True
        assert "[CARD_REDACTED]" in record.msg
        assert "4111-1111-1111-1111" not in record.msg

    def test_scrubs_ip_address_in_message(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="From 192.168.1.1 accessed",
            args=(),
            exc_info=None,
        )
        assert filt.filter(record) is True
        assert "[IP_REDACTED]" in record.msg
        assert "192.168.1.1" not in record.msg


# ---------------------------------------------------------------------------
# PIISanitizationMiddleware tests
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Pydantic DTO serialization tests removed — DTOs no longer exist in app.main.
# Endpoint tests removed — /chat/message endpoint no longer exists.
# ---------------------------------------------------------------------------
