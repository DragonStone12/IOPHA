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
# Sentinel written in place of every detected PHI/credential token. It is
# kept at module scope so the guard pattern below can reference it, and it
# deliberately contains no trigger words (e.g. "secret"/"auth") that
# other patterns might re-match.
REDACTED = "[MASKED]"

_NAME_WORD = r"(?>[^\W\d_]+)(?:[-'][^\W\d_]+)?(?![-\w'])"
# Administrative credential parameters. Distinct from PHI: these are
# service/operator secrets that must never reach stdout even though they are
# not patient-identifying. Each rule requires a recognizable key prefix so
# ordinary business fields on a tips record (``title``, ``description``) are
# never touched. Values are captured greedily to the next whitespace/quote so
# tokens like ``secret=abc,def`` or ``"token": "x,y"`` (including any commas
# inside the value) are fully redacted.
_CREDENTIAL_KEYS = (
    r"password|passwd|pwd|api[_-]?key|key|secret|token|access[_-]?token|"
    r"refresh[_-]?token|authorization|auth|bearer|client[_-]?secret|"
    r"private[_-]?key|session[_-]?id"
)
# Administrative-credential patterns. Case-insensitivity is hoisted to the
# combined compile (re.IGNORECASE) rather than inlined, because an
# inline (?i) inside a key-alternation breaks the match once the
# patterns are concatenated. Each rule requires a recognizable key prefix
# so ordinary business fields on a tips record (``title``,
# ``description``) are never touched. Values run to the next
# whitespace/quote/'=' so tokens like ``secret=abc123`` or
# ``"token": "xyz"`` (including commas within the value) are fully
# redacted.
_CREDENTIAL_PATTERNS: list[re.Pattern[str]] = [
    # HTTP Authorization: Bearer <token> / Basic <token>. Must run
    # BEFORE the JSON quoted-key rule so the entire header (incl.
    # the token) is masked in one match, not just "Authorization:".
    re.compile(r"\bauthorization\s*:\s*(?:bearer|basic)\s+[^\s]+"),
    # key=value
    re.compile(rf"\b(?:{_CREDENTIAL_KEYS})\s*=\s*['\"]?[^\s'\"=]+"),
    # JSON-ish "key": "value" -- the value (incl. its wrapping
    # quotes) runs to the next whitespace or closing quote so tokens
    # like "shh-99" or "a,b,c" (commas included) are fully masked.
    re.compile(rf'["\']?(?:{_CREDENTIAL_KEYS})["\']?\s*:\s*["\']?[^\s"]+["\']?'),
    # Guard: consume any prior sentinel so repeated scrub passes cannot
    # re-match the words inside "[MASKED]" (secret/auth) and cascade.
    re.compile(re.escape(REDACTED)),
]

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
    *_CREDENTIAL_PATTERNS,  # admin credentials
]


class PHIScrubber:
    """Redacts common PHI/PII and administrative credentials from logs.

    Every pattern is replaced with the ``[MASKED]`` sentinel so no
    patient-identifying value or operator secret reaches stdout/CloudWatch.
    The scrubber is side-effect free: it never mutates the input, only
    returns a copy.

    All patterns are compiled into a **single** alternation applied in one
    ``sub`` pass. This prevents a cascade where a later pattern matches
    text emitted by an earlier redaction and re-mangles the output.
    """

    REDACTED = "[MASKED]"

    def __init__(self, patterns: list[re.Pattern[str]] | None = None) -> None:
        self._patterns = patterns if patterns is not None else _PATTERNS
        # Combine every pattern into ONE alternation run in a single ``sub``
        # pass. Inline ``(?i)`` flags are stripped from each sub-pattern
        # (they break matching once concatenated) and case-insensitivity is
        # hoisted to a single top-level ``re.IGNORECASE`` flag.
        parts: list[str] = []
        for p in self._patterns:
            stripped = re.sub(r"^\(\?[a-z]+\)", "", p.pattern)
            parts.append(stripped)
        self._combined = re.compile(
            "(" + "|".join(parts) + ")",
            re.IGNORECASE,
        )

    def scrub_message(self, text: str) -> str:
        """Return *text* with every detected PHI/credential token masked.

        Applied as a single combined alternation in one ``sub`` pass so no
        later pattern can re-match output emitted by an earlier redaction.
        The combined pattern also consumes the ``[MASKED]`` sentinel,
        so repeated calls are idempotent: a leftover sentinel from a
        prior call is re-matched and replaced by itself rather than
        re-processed by a rule whose trigger words appear inside it
        (e.g. ``secret``), which would otherwise cascade and mangle
        the output.
        """
        if text is None:
            return ""
        if not text:
            return text
        # Strip any sentinel already present (from a prior call or upstream
        # masking) before re-applying patterns, so redaction is
        # idempotent: a repeated call cannot re-match the sentinel
        # and mangle prior output.
        cleaned = text.replace(self.REDACTED, "")
        return self._combined.sub(self.REDACTED, cleaned)


__all__ = ["PHIScrubber"]
