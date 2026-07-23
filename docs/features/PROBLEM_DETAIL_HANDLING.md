# Frontend ProblemDetail Handling

How the IOPHA frontend consumes the backend's RFC-7807 `ProblemDetail` error
payloads and surfaces them to users as toast notifications.

Companion documents:

- [RUNBOOKS.md](../RUNBOOKS.md) — the 23 backend errors this spec handles; every
  `help_url` deep-links there.
- [APPOINTMENT_FLOW.md](APPOINTMENT_FLOW.md) — error UX expectations for the
  booking flow (409 toasts, retry behavior).

## Table of Contents

| #   | Section                                             | Description                                        |
| --- | --------------------------------------------------- | -------------------------------------------------- |
| 1   | [Contract](#1-contract)                            | What the backend guarantees                        |
| 2   | [Detection & Parsing](#2-detection--parsing)       | Turning HTTP responses into typed errors           |
| 3   | [Classification](#3-classification)                | Status/title → severity and UX action              |
| 4   | [Placement Strategy](#4-placement-strategy)        | Chat-surface vs appointment-surface positioning    |
| 5   | [Toast Dispatch](#5-toast-dispatch)                | Who is allowed to raise a toast                    |
| 6   | [Handling Matrix](#6-handling-matrix)              | Per-error behavior and placement                   |
| 7   | [Non-ProblemDetail Failures](#7-non-problemdetail-failures) | Network errors, API Gateway 5xx          |
| 8   | [Privacy & Logging](#8-privacy--logging)           | What may appear in toasts and logs                 |
| 9   | [Testing Requirements](#9-testing-requirements)    | What must be asserted                              |

## 1. Contract

Every application-level error from the backend is an RFC-7807 `ProblemDetail`
JSON body emitted by the global exception handlers:

```json
{
  "title": "Time Slot Unavailable",
  "status": 409,
  "detail": "The requested slot has already been reserved.",
  "instance": "/api/providers/prov-1/slots/slot-9/reserve",
  "help_url": "https://.../RUNBOOKS.md#time-slot-unavailable"
}
```

Guarantees the frontend may rely on:

- `status` is always present and matches the HTTP status code.
- `title` is stable per error type — safe to use as a mapping key (do **not**
  match on `detail`, which is free text).
- `detail` is user-safe by construction (`safe_detail()` on the backend). It
  never contains stack traces, internals, or PHI.
- `help_url` deep-links into the matching RUNBOOKS section. The frontend
  renders it as a "Learn more" action and must not hardcode runbook URLs.
- Validation failures (`422`) additionally carry an `errors` array with
  field-level `{ field, message, type }` entries.
- The `X-Request-ID` response header echoes the correlation id for support
  references.

The frontend should also **send** `X-Request-ID` (a fresh UUID per request) so
user reports can be correlated with CloudWatch logs end-to-end.

## 2. Detection & Parsing

All API calls go through a single fetch wrapper built on `apiUrl()`
(`src/utils/api.ts`). No component calls `fetch` directly.

The wrapper's responsibilities, in order:

1. Attach the `X-Request-ID` header (new UUID per request).
2. Execute the request.
3. If `response.ok`, return the parsed body.
4. Otherwise attempt to parse the body as `ProblemDetail`:
   - Parse succeeds and `title` + `status` are present → throw a typed
     `ProblemDetailError` carrying the payload, the HTTP status, and the
     echoed request id.
   - Parse fails or the shape is wrong (API Gateway 502 HTML, empty body) →
     synthesize a fallback `ProblemDetailError` from the status code alone
     (§7).
5. Network failure (`fetch` rejects) → synthesize a status-`0`
   `ProblemDetailError` meaning "offline / unreachable" (§7).

`ProblemDetailError` is the **only** error type that escapes the API layer.
Callers never inspect `Response` objects or parse error bodies themselves.

## 3. Classification

A pure mapping function converts a `ProblemDetailError` into a toast
descriptor:

```
ProblemDetailError → { severity, message, action?, persistence, placement }
```

Severity derives from `status` first, with per-`title` overrides:

| Status class         | Default severity | Rationale                                  |
| -------------------- | ---------------- | ------------------------------------------ |
| 400, 404, 413, 422   | error            | User action required                       |
| 409, 410             | warning          | Transient state conflict; recoverable      |
| 500, 502, 503, 504   | error            | System fault; offer retry                  |
| 0 (network)          | warning          | Offline; auto-resolves on reconnect        |

Toast content rules:

- Message = the `detail` field, verbatim. It is user-safe (§1).
- Fallback when `detail` is empty: a generic per-status string ("Something
  went wrong. Please try again.").
- 5xx toasts include the request id ("Reference: abc123…") so support can
  locate the CloudWatch entry.
- `help_url` renders as a "Learn more" link action when present.
- Warnings auto-dismiss; errors persist until dismissed or resolved.

## 4. Placement Strategy

Notifications use **react-toastify**. Its multi-container support maps
directly onto the two placements: each `<ToastContainer>` gets a
`containerId`, and the dispatcher routes toasts by passing the matching
`containerId` to `toast()`.

Dependency: add `react-toastify` to `IOPHA-frontend` and import
`react-toastify/dist/ReactToastify.css` once at the app root.

Toasts render in one of two containers, chosen by the **surface that raised
the error**, not by the error type alone:

| Placement   | react-toastify container | Used for                          |
| ----------- | ------------------------ | --------------------------------- |
| `chat`      | `<ToastContainer containerId="chat" position="bottom-center">` rendered inline **under the chat input box**, inside `ChatArea.tsx` | Errors from the chat surface: messaging, attachments, and chat-initiated searches/evaluations |
| `top-right` | `<ToastContainer containerId="top-right" position="top-right">` mounted once at the app root | Errors on appointment-related screens (provider selection, time selection, confirmation, intake form) and everything else |

Rules:

- The classification mapper (§3) assigns a default `placement` per error
  `title`; the matrix in §6 records it.
- **Call sites may override the default.** Placement follows the surface the
  user is on: a provider search run from the chat thread toasts under the
  input box, while the same failure on a directory screen toasts top-right.
- The chat container renders inline beneath the input box with toasts
  stacking **bottom-center** within that region. It never overlays the
  message thread and never blocks typing. Warnings auto-dismiss
  (`autoClose`); errors use `autoClose: false` and persist until dismissed or
  the underlying condition resolves (e.g. the WebSocket banner is dismissed
  programmatically on reconnect via `toast.dismiss()`).
- The top-right viewport uses react-toastify defaults (`newestOnTop`,
  `limit: 3`; overflow is queued by the library).
- Both containers are fed by the same dispatcher (§5); placement is a
  `containerId` route, not a second notification system.

## 5. Toast Dispatch

One dispatcher module owns all notifications. It is a thin wrapper around
react-toastify's imperative `toast()` API — not a React hook tied to a
component tree — so it can be called from three places:

1. **The fetch wrapper's mutation path** — write operations (booking, intake,
   nutrition) toast failures at the call site via react-query's `onError`.
2. **react-query global handlers** — `QueryCache`/`MutationCache` `onError`
   callbacks in `QueryProvider.tsx` catch anything a component forgot.
3. **AppErrorBoundary** — only for non-API render faults; it does not toast
   API errors (they never reach the boundary).

The dispatcher translates the §3 descriptor into react-toastify options:
severity → `toast.error` / `toast.warn` / `toast.info`, persistence →
`autoClose`, placement → `containerId`, `help_url` → a "Learn more" link in
the toast body.

Deduplication (required, because react-query `retry: 1` and React strict-mode
double-invocation can fire the same failure twice) uses react-toastify's
built-in `toastId` semantics:

- `toastId = kebab(title) + instance`. react-toastify ignores a second
  `toast()` call with an id that is already displayed, so identical failures
  within the toast's lifetime raise no duplicate.
- A query-key invalidation triggered by a toast action (e.g. "refresh
  availability") calls `toast.dismiss(toastId)` first, allowing a fresh toast
  if the retry fails again.

## 6. Handling Matrix

Per-error behavior, keyed on `title`. "Refresh" means invalidate the relevant
react-query keys so stale state is re-fetched. "Placement" is the default
container from §4 (`chat` = under the input box, `top-right` = global
viewport).

### Booking & scheduling — appointment screens, all `top-right`

| Title                        | Status | Toast    | Additional behavior                                    |
| ---------------------------- | ------ | -------- | ------------------------------------------------------ |
| Time Slot Unavailable        | 409    | error    | Refresh provider slots; return to time selection       |
| Race Condition (Double Booking) | 409 | error    | Same as Time Slot Unavailable (identical UX)           |
| Schedule Lock Conflict       | 409    | warning  | Refresh slots; return to time selection                |
| Availability Drift           | 409    | warning  | Refresh slots; force list re-render                    |
| Expired Booking Session      | 410    | warning  | Persistent; clear held slot; restart booking flow      |
| Overlapping Modifier Conflict| 409    | error    | Show conflicting slot id from `detail`                 |
| Invalid Time Slot Format     | 400    | error    | Log full payload — indicates a client bug              |
| Invalid View Transition      | 409    | error    | Navigate to the expected view named in `detail`        |
| Time Zone Mismatch           | 400    | warning  | Prompt user to check device timezone                   |

### Intake & nutrition — intake on appointment screens, nutrition in chat

| Title                            | Status | Toast  | Placement | Additional behavior                             |
| -------------------------------- | ------ | ------ | --------- | ----------------------------------------------- |
| Unprocessable Content Exception  | 422    | inline | top-right | Map `errors[]` to form fields; toast only without form context |
| Intake Processing Failure        | 422    | inline | top-right | Same; `errors[]` drives field-level messages    |
| Nutrition Evaluation Error       | 500    | error  | chat      | Offer retry; include request id                 |

### Provider discovery & content — placement by surface

| Title                     | Status | Toast   | Placement  | Additional behavior                        |
| ------------------------- | ------ | ------- | ---------- | ------------------------------------------ |
| Provider Not Found        | 404    | error   | top-right  | Navigate back to directory listing         |
| Tip Not Found             | 404    | warning | top-right  | Refresh tips list (booking-tip cards)      |
| Search Aggregator Timeout | 504    | warning | chat       | Suggest refining the query; offer retry    |

Provider and tip lookups happen on appointment screens (`top-right`); the
doctor search runs inside the chat thread (`chat`).

### Chat / realtime / uploads — chat surface, all `chat`

| Title                   | Status | Toast   | Additional behavior                              |
| ----------------------- | ------ | ------- | ------------------------------------------------ |
| WebSocket Connection Drop | 503  | warning | Persistent banner under input until reconnect succeeds; backoff with jitter |
| Payload Too Large       | 413    | error   | State the size limit; suggest compressing/splitting |
| Notification Gateway Timeout | 504 | info | Non-blocking; message may arrive late            |

### Not toasted (handled silently)

These never raise a toast — the user cannot act on them:

| Title                            | Status | Surface | Handling                                  |
| -------------------------------- | ------ | ------- | ----------------------------------------- |
| Out of Order Message Delivery    | 409    | chat    | Sort messages by sequence client-side; log |
| Unread Notification Inconsistency| 409    | chat    | Reconcile unread count from server on focus; log |
| Upstream Webhook Failure         | 502    | n/a     | Log only; backend/ops reconciliation      |

### Catch-all — `top-right` unless raised from the chat surface

| Title                 | Status | Toast | Additional behavior                       |
| --------------------- | ------ | ----- | ----------------------------------------- |
| Internal Server Error | 500    | error | Generic message + request id + `help_url` |
| *(unrecognized title)*| any    | per status class (§3) | Log the unknown title for spec drift detection |

## 7. Non-ProblemDetail Failures

The backend contract covers application errors only. Three failure modes
arrive without a `ProblemDetail` body and must be synthesized by the fetch
wrapper:

| Failure                          | Synthesized as            | Toast behavior                              |
| -------------------------------- | ------------------------- | ------------------------------------------- |
| Network down / CORS / DNS        | status `0`, title `Network Unreachable` | warning, auto-dismiss on successful retry |
| API Gateway 5xx (Lambda crash, no JSON body) | status from response, title `Service Unavailable` | error with retry action |
| Malformed JSON in error body     | status from response, title `Unexpected Error` | error; log raw body (truncated) for debugging |

## 8. Privacy & Logging

- Toast messages come exclusively from `detail` — already scrubbed server-side
  (`PHIScrubber`). The frontend never interpolates request payloads, form
  values, or patient data into toast text.
- `logger.ts` error entries for API failures record: `title`, `status`,
  `instance`, request id. **Never** `detail` combined with request payloads,
  and never response bodies.
- 400/422 errors log at `warn` (client fault); 5xx at `error` (system fault).
- The request id shown in 5xx toasts is the same UUID sent as `X-Request-ID`,
  so a user screenshot gives support the CloudWatch lookup key. It is an
  opaque UUID, not PHI.

## 9. Testing Requirements

Component tests (Cypress) must assert, with `@swimlane/cy-mockapi` stubbing
each status:

- [ ] Each matrix row in §6 renders the expected severity and message.
- [ ] Chat-surface errors (§6) render bottom-center in the inline region
      under the chat input box, never in the top-right viewport, and never
      overlay the message thread.
- [ ] Appointment-screen errors (§6) render in the top-right viewport, never
      under the chat input.
- [ ] The WebSocket drop banner persists under the input and clears on
      reconnect.
- [ ] 409 booking errors trigger slot-list invalidation (list re-fetches).
- [ ] 422 errors render inline field messages, not toasts, inside a form.
- [ ] Identical failures produce exactly one toast (same `toastId` is a no-op
      while displayed).
- [ ] Non-ProblemDetail failures (network, HTML 502) produce the synthesized
      fallback toasts from §7.
- [ ] No toast appears for the three silent errors in §6.
- [ ] Toast text never contains stubbed PHI values (mirror the backend's
      leak-marker assertions).
- [ ] Unknown `title` values fall back to status-class severity and are logged.
