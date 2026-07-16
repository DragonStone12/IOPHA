# IOPHA Runbooks — Error Mitigation Guide

This document is the centralized troubleshooting reference for the IOPHA
backend. Every structured error response emitted by the global exception
handlers includes a `help_url` that deep-links directly to the section below
matching the fault. The `help_url` link MUST stay in sync with the markdown
header slugs in this file (GitHub lowercases headers, replaces spaces with
hyphens, and strips punctuation).

| Error | Status Code | Link |
| --- | --- | --- |
| Race Condition (Double Booking) | 409 | [race-condition-double-booking](#race-condition-double-booking) |
| Time Zone Mismatch | 400 | [time-zone-mismatch](#time-zone-mismatch) |
| Availability Drift | 409 | [availability-drift](#availability-drift) |
| Overlapping Modifier Conflict | 409 | [overlapping-modifier-conflict](#overlapping-modifier-conflict) |
| WebSocket Connection Drop | 503 | [websocket-connection-drop](#websocket-connection-drop) |
| Out of Order Message Delivery | 409 | [out-of-order-message-delivery](#out-of-order-message-delivery) |
| Unread Notification Inconsistency | 409 | [unread-notification-inconsistency](#unread-notification-inconsistency) |
| Payload Too Large | 413 | [payload-too-large](#payload-too-large) |
| External Calendar Sync Disconnect | 502 | [external-calendar-sync-disconnect](#external-calendar-sync-disconnect) |
| Upstream Webhook Failure | 502 | [upstream-webhook-failure](#upstream-webhook-failure) |
| Notification Gateway Timeout | 504 | [notification-gateway-timeout](#notification-gateway-timeout) |
| Invalid View Transition | 409 | [invalid-view-transition](#invalid-view-transition) |
| Expired Booking Session | 410 | [expired-booking-session](#expired-booking-session) |
| Provider Not Found | 404 | [provider-not-found-error](#provider-not-found-error) |
| Tip Not Found | 404 | [tip-not-found-error](#tip-not-found-error) |
| Time Slot Unavailable | 409 | [time-slot-unavailable](#time-slot-unavailable) |
| Schedule Lock Conflict | 409 | [schedule-lock-conflict](#schedule-lock-conflict) |
| Invalid Time Slot Format | 400 | [invalid-time-slot-format](#invalid-time-slot-format) |
| Search Aggregator Timeout | 504 | [search-aggregator-timeout](#search-aggregator-timeout) |
| Nutrition Evaluation Error | 500 | [nutrition-evaluation-error](#nutrition-evaluation-error) |
| Unprocessable Entity Exception | 422 | [unprocessable-entity-error](#unprocessable-entity-error) |
| Intake Processing Failure | 422 | [intake-processing-error](#intake-processing-error) |
| Internal Server Error | 500 | [internal-server-error](#internal-server-error) |

## Race Condition Double Booking

**What happened:** Two transactions committed the same appointment slot in the
same instant before row-level locking resolved the conflict, producing a
double-booking.

**Common causes:**
- Missing `SELECT ... FOR UPDATE` / optimistic concurrency token on the slots table.
- Two concurrent requests racing on a cached availability read.

**Mitigation:**
1. Introduce pessimistic row locking or a unique constraint on `(slot_id, date)` at write time.
2. Add an optimistic-concurrency `version` column and retry on conflict.
3. Return the conflict to the client; never silently overwrite the existing booking.

## Time Zone Mismatch

**What happened:** A timestamp was stored or parsed in the wrong time zone
(local vs UTC), shifting the appointment by hours on the patient's calendar.

**Common causes:**
- Backend persisting naive local time instead of UTC.
- Client rendering a UTC timestamp without converting to the user's locale.

**Mitigation:**
1. Store and transport all times in UTC (ISO-8601 with `Z`).
2. Convert to the patient's timezone only at the presentation layer.
3. Validate the account/device timezone configuration.

## Availability Drift

**What happened:** The user was shown an open slot from a cached availability
list, but the slot was already booked; the confirm write failed.

**Common causes:**
- Stale cache entry not invalidated on booking.
- Read-after-write inconsistency between cache and database.

**Mitigation:**
1. Invalidate the availability cache entry on every successful booking.
2. Re-validate slot availability inside the write transaction before commit.
3. Surface a clear "slot gone" message and force a refresh.

## Overlapping Modifier Conflict

**What happened:** An appointment's duration was extended (e.g. 30 -> 60 min),
bleeding into an already-booked following appointment.

**Common causes:**
- Duration change applied without re-checking adjacent bookings.
- No overlap constraint on the scheduling window.

**Mitigation:**
1. Re-run the overlap check whenever duration changes.
2. Reject or auto-shift the appointment when it collides with the next slot.
3. Return the conflicting slot id to the client for correction.

## WebSocket Connection Drop

**What happened:** The realtime chat socket disconnected (e.g. Wi-Fi to 5G
handoff) and the client did not reconnect.

**Common causes:**
- No exponential backoff reconnect strategy on the client.
- Socket leak from unclosed listeners on disconnect.

**Mitigation:**
1. Implement exponential backoff with jitter on the client.
2. Tear down listeners/subscriptions on `close` to avoid socket leaks.
3. Replay missed messages on reconnect using the last seen sequence.

## Out of Order Message Delivery

**What happened:** Message B rendered before message A due to async latency or
poor backend indexing.

**Common causes:**
- Missing sequence/monotonic index on messages.
- Client appending messages by arrival instead of order.

**Mitigation:**
1. Stamp every message with a monotonic sequence/server timestamp.
2. Sort client-side by sequence before rendering.
3. De-duplicate by message id.

## Unread Notification Inconsistency

**What happened:** The user read a message but the read receipt never reached
the server, leaving a stale "1 unread" badge across devices.

**Common causes:**
- Service worker dropped the acknowledgment.
- Local state updated without confirming server receipt.

**Mitigation:**
1. Send the read receipt idempotently and await server ACK.
2. Reconcile unread counts from the server on focus/refresh.
3. Make the badge derived from server state, not local optimistic state.

## Payload Too Large

**What happened:** A chat attachment (insurance card, medical record) exceeded
the backend's maximum multipart upload size, returning 413.

**Common causes:**
- Upload exceeds `client_max_body_size` / multipart limit.
- No pre-upload size check on the client.

**Mitigation:**
1. Enforce and document the max upload size.
2. Compress/split large files on the client before upload.
3. Return the limit in the error detail so the client can guide the user.

## External Calendar Sync Disconnect

**What happened:** The linked Google/Outlook calendar disconnected because the
OAuth refresh token expired or was revoked; slots are still booked locally.

**Common causes:**
- Refresh token expired, revoked, or scoped incorrectly.
- No proactive token-health check before booking.

**Mitigation:**
1. Detect token expiry and prompt re-authorization.
2. Add a token-refresh health check before synchronizing bookings.
3. Flag locally-booked slots that could not be pushed to the provider.

## Upstream Webhook Failure

**What happened:** A cancellation processed locally but the webhook to the
external EHR failed, leaving the appointment active in the secondary ledger.

**Common causes:**
- EHR endpoint timeout or 5xx.
- No durable retry/queue for outbound webhooks.

**Mitigation:**
1. Put outbound webhooks on a durable retry queue with backoff.
2. Alert on repeated webhook failures.
3. Reconcile the secondary ledger on the next sync cycle.

## Notification Gateway Timeout

**What happened:** An SMS/push notification (Twilio/FCM) timed out or hit a rate
limit, so the user was not notified of the booking or message.

**Common causes:**
- Gateway latency / upstream 5xx.
- Provider rate-limit exceeded.

**Mitigation:**
1. Retry with backoff and respect provider rate limits.
2. Fall back to an alternate channel when one times out.
3. Track delivery status and surface non-delivery to the user.

## Invalid View Transition

**What happened:** The frontend and backend disagreed on the current booking or
chat phase (e.g. clicking "Book Now" mid-transition with a missing provider id).

**Common causes:**
- Frontend forced a view change without required state (provider id undefined).
- No server-side guard on the expected state machine phase.

**Mitigation:**
1. Guard every transition server-side against the expected phase.
2. Validate required identifiers before allowing the transition.
3. Return the current and expected views so the client can recover.

## Expired Booking Session

**What happened:** The temporary slot hold was released after the session
timeout, but the frontend never notified the user; submit then failed.

**Common causes:**
- Hold TTL (10 min) elapsed during form fill / payment.
- Frontend did not subscribe to hold-expiry events.

**Mitigation:**
1. Push hold-expiry notifications to the client before TTL.
2. Show a countdown and re-acquire the hold on activity.
3. Return 410 with the released slot id so the user restarts cleanly.

## Provider Not Found Error

**What happened:** A client requested a physician/provider entity by id
(`GET /api/providers/{provider_id}`) but the repository returned no matching
record, so the service raised `ProviderNotFoundException`.

**Common causes:**
- Typo'd or stale provider id in the frontend route / cache.
- The provider was deactivated or never existed in the directory source.
- A test or integration hitting the real repository with an un-seeded id.

**Mitigation:**
1. Verify the `provider_id` passed by the client matches an active directory record.
2. Confirm the provider repository is wired to the correct datasource for the environment.
3. Return the canonical directory listing so the client can re-select a valid provider.

## Tip Not Found Error

**What happened:** A client requested a single dynamic booking tip / advice
node by id (`GET /api/tips/{tip_id}`) but the tips repository
returned no matching record, so the service raised
`TipNotFoundException`.

**Common causes:**
- A typo or stale tip id in the frontend route / cache.
- The tip was removed or never existed in the tips source.
- A test or integration hitting the real repository with an un-seeded id.

**Mitigation:**
1. Verify the `tip_id` passed by the client matches an active tips record.
2. Confirm the tips repository is wired to the correct datasource for the environment.
3. Surface a clear "tip gone" message and re-fetch the active tips list.

## Unprocessable Entity Exception

**What happened:** The client sent a syntactically valid request, but the server
could not process it because one or more fields failed validation (wrong type,
missing required field, format violation, or out-of-range value). FastAPI
returns this as `RequestValidationError`, which the global handler projects
into a single RFC-7807 `ProblemDetail` payload.

**Common causes:**
- Missing required field in the JSON body or query parameters.
- Type mismatch (`"age": "twenty-five"` instead of a number).
- String or enum format violation (bad email, unknown enum value).
- Value outside an allowed range or length constraint.

**Mitigation:**
1. Inspect the `errors` array in the response for the exact field, message, and
   validation type.
2. Correct the payload according to the API schema before retrying.
3. Validate client-side against the OpenAPI `ProblemDetail` contract so the
   frontend surfaces field-level errors before the request is sent.

## Intake Processing Failure

**What happened:** The patient intake profile pipeline failed to validate or
ingest the submitted profile. The global handler projected the failure into an
RFC-7807 `ProblemDetail` payload with a `help_url` runbook link.

**Common causes:**
- Phone number did not contain exactly 10 numerical digits after stripping
  non-digit characters.
- Email address did not match the expected format.
- Required field (`name`, `email`, or `phone`) was missing from the payload.
- An unplanned field was included in the request body (the schema enforces
  `extra="forbid"`).
- The intake service raised `IntakeProcessingException` after schema validation
  passed (e.g., downstream processing constraint violation).

**Mitigation:**
1. Inspect the `errors` array in the response for the exact field and message.
2. Correct the payload according to the `PatientDataSchema` contract before
   retrying.
3. Ensure the phone field contains exactly 10 digits and the email matches the
   standard format.
4. If the failure persists after payload correction, check the structured
   server logs for the `requestId` and the `intake.processing_failure` event
   to identify the offending request.

## Internal Server Error

**What happened:** An unhandled runtime fault broke execution context.

**What to do (developers):**
1. Find the `requestId` in the structured server logs and search CloudWatch/ES.
2. Inspect the `exc_info` trace captured server-side for this request.
3. Reproduce using the request path and headers; never rely on the client
   `detail` (it is intentionally generic and contains no stack trace).

## Time Slot Unavailable

**What happened:** A patient attempted to reserve a time slot that has already
been booked by another patient or released by the system.

**Common causes:**
- Two patients reserved the same slot concurrently before row-level locking
  resolved the conflict.
- The slot was held beyond its TTL and automatically released.
- A stale availability cache returned a slot that was no longer bookable.

**Mitigation:**
1. Re-fetch the provider's available slots and present the refreshed list.
2. Return the conflict to the client with a clear "slot gone" message and force
   a refresh.
3. Log `slotId` and `providerId` for audit trail correlation.

## Schedule Lock Conflict

**What happened:** The booking confirmation transaction lost an optimistic lock
race. The slot appeared available when the request started, but another
patient's transaction reserved it before this request could commit.

**Common causes:**
- Two concurrent confirmation requests targeted the same remaining slot.
- The availability cache was stale when the user clicked "Confirm".
- Row-level locking on the slot table is missing or misconfigured.

**Mitigation:**
1. Treat this as a transient race condition, not a permanent failure.
2. Return the user to the time-selection view with refreshed availability.
3. Verify the reservation layer uses an atomic compare-and-swap or database
   constraint to prevent silent double-bookings.

## Invalid Time Slot Format

**What happened:** The client supplied a slot identifier or time string that
does not conform to the expected `YYYY-MM-DD-h:MM AM/PM` format.

**Common causes:**
- Frontend slug-encoding or URL-decoding transformed the slot id.
- A calendar integration emitted a non-civil time format (24-hour clock,
  lowercase AM/PM).
- The slot id was manually constructed or copy-pasted incorrectly.

**Mitigation:**
1. Inspect the `details` field in the response for the exact format violation.
2. Correct the slot id to match the `TimeSlotSchema.id` pattern before retrying.
3. Ensure client-side formatting uses the same 12-hour civil time pattern
   (`0[1-9]|1[0-2]:[0-5][0-9] (AM|PM)`) as the backend validator.

## Nutrition Evaluation Error

**What happened:** The nutrition evaluation engine failed to produce a
structured `NutritionResponseDataSchema` for the requested profile, so
the endpoint returned 500 instead of a populated response.

**Common causes:**
- The profile payload was corrupted or failed downstream validation.
- The evaluation engine dependency raised during processing.
- A fault-injected test double raised to exercise the error path.

**Mitigation:**
1. Inspect the structured server logs for the `requestId` and the
   `nutrition.evaluation_engine_error` event to identify the offending
   `profileId`.
2. Check the health of the nutrition evaluation dependency and retry
   with a narrower or corrected profile if possible.
3. If the engine is degraded, surface the clear 500 message to the
   client and suggest retrying later.

## Search Aggregator Timeout

**What happened:** The provider discovery aggregator failed to return
parameters within the execution time bound, so the search endpoint returned
504 instead of a populated `FindDoctorResponseDataSchema`.

**Common causes:**
- Upstream provider directory or index service is unhealthy or overloaded.
- Network partition between the backend and the discovery microservice.
- Query complexity or missing index caused the aggregation pipeline to exceed
  the configured timeout threshold.

**Mitigation:**
1. Inspect the structured server logs for the `requestId` and the
   `search.search_aggregator_timeout` event to identify the offending query
   and upstream latency.
2. Check the health of the discovery microservice and retry with a narrower
   query if possible.
3. If the upstream is degraded, surface a clear timeout message to the client
   and suggest refining the search terms or trying again later.
