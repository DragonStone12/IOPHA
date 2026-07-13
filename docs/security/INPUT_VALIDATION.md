# Input Validation & Payload Limits

## Table of Contents

- [Overview](#overview)
- [Known Issue: Unbounded String Fields in API Schemas](#known-issue-unbounded-string-fields-in-api-schemas)
- [Resolution](#resolution)
- [Schema Limits Reference](#schema-limits-reference)
- [Testing Requirements](#testing-requirements)

## Overview

All external-facing Pydantic schemas must enforce bounded payload sizes to prevent memory exhaustion and denial-of-service (DoS) attacks. A malicious or faulty client can submit multi-megabyte payloads through unbounded string fields, consuming server memory and bandwidth.

**Defense-in-depth layers:**

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| Pydantic schema validation | `max_length` on `Field` | Rejects oversized payloads at the API boundary before business logic executes |
| OpenAPI contract | Auto-generated from schemas | Documents limits to frontend consumers so they can enforce pre-flight checks |
| Global middleware | `client_max_body_size` / upload limits | Blanket safety net for all incoming request bodies |

## Known Issue: Unbounded String Fields in API Schemas

### What was wrong

Multiple external-facing Pydantic schemas accepted unbounded string lengths:

- `TipSchema.title` — no `max_length`
- `TipSchema.description` — no `max_length`
- `PhysicianSchema.name`, `specialty`, `distance`, `nextAvailable`, `imageUrl`, `facility` — no `max_length`
- `TimeSlotSchema.label` — no `max_length`
- `ProviderSchema.name`, `specialty`, `distance`, `nextAvailable`, `imageUrl`, `facility` — no `max_length`

**Why this is wrong:**

1. **DoS vulnerability.** A client can submit arbitrarily large strings (megabytes or larger) that consume server memory during Pydantic validation, JSON serialization, and response streaming.
2. **Bandwidth exhaustion.** Large responses increase egress costs and can saturate client connections.
3. **Violates defensive validation posture.** The schemas already enforce `extra="forbid"` and pattern constraints (e.g., `TimeSlotSchema.id`). Unbounded strings are an inconsistent gap in the same defensive contract.

**Example attack vector:**

```python
# Attacker sends a 10 MB description string
POST /api/tips/123
{
  "number": 1,
  "title": "x",
  "description": "A" * 10_000_000
}
```

Without `max_length`, Pydantic accepts the payload, the service layer projects it into a response DTO, and the server streams 10 MB back to the client — all for a single advice card.

### Root cause

The schemas were designed with structural validation (`min_length`, `pattern`, `ge`) but omitted size bounds. The in-memory repositories seeded short strings, so the issue was not visible in local development. It only surfaces when a malicious or faulty client submits oversized payloads.

## Resolution

### Fix applied

Added `max_length` constraints to every unbounded string field across all external-facing schemas:

```python
# TipSchema
title: str = Field(..., min_length=1, max_length=200, ...)
description: str = Field(..., min_length=1, max_length=2000, ...)

# PhysicianSchema / ProviderSchema
name: str = Field(..., max_length=200, ...)
specialty: str = Field(..., max_length=100, ...)
distance: str = Field(..., max_length=50, ...)
nextAvailable: str = Field(..., max_length=100, ...)
imageUrl: Optional[str] = Field(None, max_length=1000, ...)
facility: Optional[str] = Field(None, max_length=200, ...)

# TimeSlotSchema
label: str = Field(..., max_length=100, ...)
```

**Why these limits:**

- **`title` / `name` (200):** Clinical headlines and physician names rarely exceed a few words. 200 chars is more than enough for realistic content.
- **`description` (2000):** Clinical advice bodies should be concise. 2000 chars supports ~300 words — sufficient for actionable guidance without enabling essay-length payloads.
- **`specialty` (100):** Medical specialties are short, standardized terms.
- **`distance` (50):** Localized distance strings (e.g., "1.8 miles") are inherently brief.
- **`nextAvailable` (100):** Timeline mappings like "Today, 3:30 PM" are short.
- **`imageUrl` (1000):** URLs can include query strings and CDN paths, so the limit is higher but still bounded.
- **`facility` (200):** Hospital/facility names can be longer than specialties but rarely exceed this.
- **`label` (100):** Time slot labels like "09:00 AM" are inherently short.

### Validation behavior

When a client submits a payload that exceeds `max_length`, Pydantic raises a `ValidationError` and FastAPI returns a structured RFC-7807 `422 Unprocessable Entity` response (via the global `RequestValidationError` handler). The client receives a clear error message identifying the offending field and constraint.

### How to choose limits for new fields

1. **Business logic first:** How much text does the feature actually need? Err on the side of tight limits.
2. **Database alignment:** If the field maps to a database column, set `max_length` to match or slightly below the column limit. This prevents database-level 500 errors from bubbling up.
3. **Frontend UX:** Document the limit in the OpenAPI schema so the frontend can enforce pre-flight checks and surface clear errors before the request is sent.

## Schema Limits Reference

| Schema | Field | Limit | Rationale |
|--------|-------|-------|-----------|
| `TipSchema` | `title` | 200 chars | Short headline |
| `TipSchema` | `description` | 2000 chars | Concise clinical advice body |
| `PhysicianSchema` | `name` | 200 chars | Full display name with credentials |
| `PhysicianSchema` | `specialty` | 100 chars | Standardized medical specialty |
| `PhysicianSchema` | `distance` | 50 chars | Localized distance string |
| `PhysicianSchema` | `nextAvailable` | 100 chars | Timeline mapping |
| `PhysicianSchema` | `imageUrl` | 1000 chars | CDN URL with query strings |
| `PhysicianSchema` | `facility` | 200 chars | Hospital/facility name |
| `TimeSlotSchema` | `label` | 100 chars | Time slot button label |
| `ProviderSchema` | `name` | 200 chars | Full display name with credentials |
| `ProviderSchema` | `specialty` | 100 chars | Standardized medical specialty |
| `ProviderSchema` | `distance` | 50 chars | Localized distance string |
| `ProviderSchema` | `nextAvailable` | 100 chars | Timeline mapping |
| `ProviderSchema` | `imageUrl` | 1000 chars | CDN URL with query strings |
| `ProviderSchema` | `facility` | 200 chars | Hospital/facility name |

## Testing Requirements

All changes to API schemas must include tests that assert:

- [ ] New `max_length` constraint rejects payloads exceeding the limit
- [ ] Valid payloads at exactly the boundary (`max_length` chars) are accepted
- [ ] Invalid payloads return `422 Unprocessable Entity` with RFC-7807 problem detail
- [ ] Existing seeded data and integration tests continue to pass
- [ ] Ruff lint passes with no `E501` line-length violations

### Example test pattern

```python
def test_rejects_description_exceeds_max_length(self) -> None:
    payload = {**_valid_tip(), "description": "x" * 2001}
    with pytest.raises(ValidationError):
        TipSchema(**payload)  # type: ignore[arg-type]
```

### Verification

Run the targeted tests:

```bash
cd IOPHA-backend
PYTHONPATH=. venv/bin/python -m pytest tests/unit/test_tip_schema.py tests/unit/test_timeslot_schema.py tests/integration/test_schema_integration.py -v
```

All schema and integration tests must pass.
