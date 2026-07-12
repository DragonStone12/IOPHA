import time

from app.core.phi_scrubber import PHIScrubber

REDACTED = PHIScrubber.REDACTED


class TestPHIScrubber:
    def test_redacts_email(self) -> None:
        out = PHIScrubber().scrub_message("contact john.doe@example.com today")
        assert "john.doe@example.com" not in out
        assert REDACTED in out

    def test_redacts_phone(self) -> None:
        out = PHIScrubber().scrub_message("call 555-123-4567 now")
        assert "555-123-4567" not in out
        assert REDACTED in out

    def test_redacts_ssn(self) -> None:
        out = PHIScrubber().scrub_message("ssn 123-45-6789 on file")
        assert "123-45-6789" not in out
        assert REDACTED in out

    def test_redacts_dob(self) -> None:
        out = PHIScrubber().scrub_message("dob 01/15/1980 verified")
        assert "01/15/1980" not in out
        assert REDACTED in out

    def test_redacts_labeled_name(self) -> None:
        out = PHIScrubber().scrub_message("patient: Jane Doe arrived")
        assert "Jane Doe" not in out
        assert REDACTED in out

    def test_leaves_non_phi_untouched(self) -> None:
        # Calendar slot ids embed ISO dates; they must NOT be redacted.
        text = "slot 2024-01-15-09:00 AM is available"
        assert PHIScrubber().scrub_message(text) == text

    def test_leaves_ordinary_two_word_phrase_untouched(self) -> None:
        # "Time Slot" is a legitimate app term, not a patient name.
        assert PHIScrubber().scrub_message("Time Slot selected") == "Time Slot selected"

    def test_empty_string_returns_empty(self) -> None:
        assert PHIScrubber().scrub_message("") == ""

    def test_performance_minimal_overhead(self) -> None:
        scrubber = PHIScrubber()
        text = (
            "email a@b.com phone 555-123-4567 ssn 123-45-6789 "
            "dob 01/15/1980 patient: John Doe"
        )
        start = time.perf_counter()
        for _ in range(1000):
            scrubber.scrub_message(text)
        per_call = (time.perf_counter() - start) / 1000
        # Well under the 5ms/line budget; generous bound avoids CI flakiness.
        assert per_call < 0.01
