import re

# Conservative PHI patterns. We deliberately avoid an ISO-date rule
# (YYYY-MM-DD) because calendar slot ids embed real ISO dates
# (e.g. ``2024-01-15-09:00 AM``); redacting those would corrupt legitimate
# availability logs. DOB is therefore matched only in the US civil form
# (MM/DD/YYYY), and names only when introduced by a recognizable label so we
# do not over-redact ordinary two-capitalized-word phrases.
# A "name word" is letters, optionally followed by a single hyphen or
# apostrophe and more letters -- but it must NOT be followed by another
# hyphen/word char. That lookahead is what keeps multi-hyphen system
# identifiers (e.g. ``primary-db-replica``) intact: a ``word-word-word``
# chain has 2+ hyphens, so once the regex sees the second hyphen it fails
# the lookahead and the whole value is left alone, while real names
# (``Mary-Jane``, ``O'Connor``) still redact.
_NAME_WORD = r"(?>[^\W\d_]+)(?:[-'][^\W\d_]+)?(?![-\w'])"
_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),  # email
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN
    re.compile(r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"),  # phone
    re.compile(
        r"\b(0[1-9]|1[0-2])[/-](0[1-9]|[12]\d|3[01])[/-]\d{4}\b"
    ),  # DOB MM/DD/YYYY
    re.compile(
        r"\b(?:name|patient|member|contact|dob)\s*[:=]\s*"
        rf"(?:{_NAME_WORD}(?:\s+{_NAME_WORD}){{0,3}})",
    ),
]


class PHIScrubber:
    """Redacts common PHI/PII from log messages and structured fields.

    Every pattern is replaced with the ``[REDACTED]`` sentinel so no
    patient-identifying value reaches stdout/CloudWatch. The scrubber is
    side-effect free: it never mutates the input, only returns a copy.
    """

    REDACTED = "[REDACTED]"

    def __init__(self, patterns: list[re.Pattern[str]] | None = None) -> None:
        self._patterns = patterns if patterns is not None else _PATTERNS

    def scrub_message(self, text: str) -> str:
        """Return *text* with every detected PHI token replaced by ``[REDACTED]``."""
        if not text:
            return text
        result = text
        for pattern in self._patterns:
            result = pattern.sub(self.REDACTED, result)
        return result


__all__ = ["PHIScrubber"]
