# Sensitive Data Handling

## Table of Contents

- [Overview](#overview)
- [PHI/PII Redaction Architecture](#phipii-redaction-architecture)
- [Credential Scrubbing](#credential-scrubbing)
- [Known Issue: Destructive Sentinel Stripping in PHIScrubber](#known-issue-destructive-sentinel-stripping-in-phiscrubber)
- [Resolution](#resolution)
- [Testing Requirements](#testing-requirements)

## Overview

IOPHA handles Protected Health Information (PHI), Personally Identifiable Information (PII), and administrative credentials. A defense-in-depth sanitization strategy prevents accidental exposure in logs, metrics, and API responses.

**Three-layer sanitization stack:**

| Layer | Component | Purpose |
|-------|-----------|---------|
| HTTP Transport Middleware | `PIISanitizationMiddleware` | Normalizes dynamic URL paths and redacts sensitive query parameters before logging/metrics middleware sees them |
| Logging Filter | `PIISanitizerFilter` | Intercepts all `LogRecord` objects before JSON serialization and redacts email, phone, SSN, and labeled names |
| PHI Scrubber | `PHIScrubber` (`app/core/phi_scrubber.py`) | Redacts PHI/PII and administrative credentials from log messages using compiled regex patterns |

## PHI/PII Redaction Architecture

### PHIScrubber

`PHIScrubber` is a side-effect-free redactor that returns a copy of the input with every detected PHI/credential token replaced by the `[MASKED]` sentinel.

**Pattern categories:**

| Category | Examples | Regex Strategy |
|----------|----------|----------------|
| Contact | Email, phone | Standard format matching |
| Government IDs | SSN, DOB (MM/DD/YYYY only) | Strict civil-date format; ISO calendar dates (`YYYY-MM-DD`) are **not** redacted because `TimeSlotSchema.id` embeds real ISO dates |
| Names | Labeled names (`patient: Jane Doe`) | Requires recognizable label prefix to avoid over-redacting ordinary two-word phrases |
| Credentials | `password`, `secret`, `token`, `Authorization: Bearer` | Key-prefix rules so business fields (`title`, `description`) are never touched |

**Key design decisions:**

- **No ISO-date redaction:** Calendar slot ids embed real ISO dates (e.g. `2024-01-15-09:00 AM`). Redacting those would corrupt legitimate availability logs.
- **No blanket name redaction:** Only names introduced by recognizable labels (`name:`, `patient:`, `contact:`, `dob:`) are redacted. This prevents over-redacting phrases like "Time Slot".
- **Single alternation pass:** All patterns are combined into one regex and applied in a single `sub` pass. This prevents cascade effects where a later pattern matches text emitted by an earlier redaction.

### Idempotency Guarantee

The combined pattern includes a guard rule that matches the `[MASKED]` sentinel itself:

```python
re.compile(re.escape(REDACTED)),  # Guard: consume prior sentinel
```

When the scrubber runs on already-redacted text, the guard matches each `[MASKED]` and replaces it with itself. This prevents other patterns from re-matching trigger words inside the sentinel (e.g., `secret` inside `[MASKED]`), which would cascade and mangle output.

## Credential Scrubbing

Administrative credentials (service keys, API tokens, session IDs) are distinct from PHI but must never reach stdout. `PHIScrubber` redacts them using the same sentinel.

**Credential patterns:**

| Pattern | Example Input | Redacted Output |
|---------|--------------|-----------------|
| `key=value` | `password=hunter2` | `[MASKED]` |
| JSON `"key": "value"` | `{"secret": "shh-99"}` | `{[MASKED]}` |
| `Authorization: Bearer` | `Authorization: Bearer eyJabc` | `[MASKED]` |

Each credential rule requires a recognizable key prefix so legitimate business data is never touched.

## Known Issue: Destructive Sentinel Stripping in PHIScrubber

### What was wrong

The original `scrub_message` implementation attempted to make redaction idempotent by stripping existing `[MASKED]` sentinels before re-applying patterns:

```python
# WRONG — destroys legitimate [MASKED] strings
cleaned = text.replace(self.REDACTED, "")
return self._combined.sub(self.REDACTED, cleaned)
```

**Why this is wrong:**

1. **Data loss.** If the original, unredacted text legitimately contains the string `[MASKED]`, it is removed entirely. The surrounding text is then re-processed by the regex patterns, corrupting non-PHI content.
2. **Violates the scrubber contract.** `PHIScrubber` is documented as side-effect free: it never mutates input, only returns a copy. Stripping content from the input violates this guarantee.
3. **Unnecessary.** The combined pattern already includes a guard rule for the sentinel, making the pre-strip step redundant.

**Example of data corruption:**

```python
PHIScrubber().scrub_message("status: [MASKED] pending review")
# Original buggy output: "status:  pending review"  ← [MASKED] was deleted
# Expected output:        "status: [MASKED] pending review"  ← preserved
```

### Root cause

The author conflated "idempotency" (safe to run multiple times) with "strip prior output." True idempotency is achieved when repeated calls produce the same result without side effects — not when the function destructively removes its own sentinel.

## Resolution

### Fix applied

The destructive `text.replace(self.REDACTED, "")` line was removed. The guard pattern already present in `_CREDENTIAL_PATTERNS` handles idempotency correctly by matching `[MASKED]` and replacing it with itself:

```python
def scrub_message(self, text: str) -> str:
    if not text:
        return text
    return self._combined.sub(self.REDACTED, text)
```

**Why this works:**

- **No data loss.** Legitimate `[MASKED]` strings in the original input are preserved because the guard pattern matches them first and replaces each with itself.
- **True idempotency.** Running the scrubber on already-redacted text is a no-op: the guard pattern consumes each `[MASKED]` and re-emits `[MASKED]`.
- **Cascade prevention.** The guard pattern prevents other rules from re-matching trigger words inside the sentinel (e.g., `secret` in `[MASKED]`).

### Verification

Run the targeted tests:

```bash
cd IOPHA-backend
PYTHONPATH=. venv/bin/python -m pytest tests/unit/test_phi_scrubber.py tests/unit/test_tips_logging.py -v
```

All 20 tests must pass, including the two new tests that explicitly verify:
- Legitimate `[MASKED]` strings are preserved
- Redaction is idempotent on already-redacted text

## Testing Requirements

All changes to `PHIScrubber` must include tests that assert:

- [ ] Legitimate `[MASKED]` strings in original input are preserved
- [ ] Redaction is idempotent: `scrub_message(scrub_message(text)) == scrub_message(text)`
- [ ] No PHI/PII or credentials appear in the output
- [ ] Non-PHI content (calendar dates, business fields) is untouched
- [ ] Empty strings return empty strings without error
