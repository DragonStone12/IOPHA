import logging

from fastapi import status

# Centralized GitHub runbook documentation. Per-error links are appended to
# this base URL to deep-link clients directly to the exact mitigation section
# in docs/RUNBOOKS.md. Anchors MUST match the GitHub-generated slug of the
# corresponding markdown header (lowercase, spaces -> hyphens, punctuation
# removed) or the link will 404.
GITHUB_RUNBOOK_BASE_URL = (
    "https://github.com/DragonStone12/IOPHA/blob/main/docs/RUNBOOKS.md"
)


class IOPHADomainError(Exception):
    """Base class for all known, domain-specific IOPHA application errors.

    Subclasses declare their Status Code, documentation link, client-safe
    title, and log metadata. Neither ``safe_detail`` nor ``log_context`` may
    include raw exception text, stack traces, memory addresses, database
    schemas, or credentials -- those are logged server-side only (never sent
    to the client).
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    link: str = "domain-error"
    title: str = "Application Error"
    log_level: int = logging.ERROR
    log_event: str = "request.domain_error"

    def safe_detail(self) -> str:
        """Return a client-safe, human-readable description of the error."""
        return "An application domain error occurred."

    def log_context(self) -> dict[str, object]:
        """Return structured, non-sensitive context for server-side logs."""
        return {}


class RaceConditionDoubleBookingError(IOPHADomainError):
    """Two transactions committed the same slot before locking resolved."""

    status_code = status.HTTP_409_CONFLICT
    link = "race-condition-double-booking"
    title = "Appointment Slot Double-Booked"
    log_level = logging.WARNING
    log_event = "scheduling.race_condition_double_booking"

    def __init__(self, slot_id: str, patient_id: str) -> None:
        super().__init__()
        self.slot_id = slot_id
        self.patient_id = patient_id

    def safe_detail(self) -> str:
        return (
            f"The requested appointment slot '{self.slot_id}' was booked by "
            "another user. Please choose a different time."
        )

    def log_context(self) -> dict[str, object]:
        return {"slotId": self.slot_id, "patientId": self.patient_id}


class TimeZoneMismatchError(IOPHADomainError):
    """Stored or parsed timestamp used the wrong timezone (local vs UTC)."""

    status_code = status.HTTP_400_BAD_REQUEST
    link = "time-zone-mismatch"
    title = "Time Zone Mismatch"
    log_level = logging.WARNING
    log_event = "scheduling.timezone_mismatch"

    def __init__(self, slot_id: str, patient_id: str) -> None:
        super().__init__()
        self.slot_id = slot_id
        self.patient_id = patient_id

    def safe_detail(self) -> str:
        return (
            "The appointment time could not be resolved to the patient's "
            "time zone. Verify the device and account timezone settings."
        )

    def log_context(self) -> dict[str, object]:
        return {"slotId": self.slot_id, "patientId": self.patient_id}


class AvailabilityDriftError(IOPHADomainError):
    """Cached availability was stale; the confirm write lost the race."""

    status_code = status.HTTP_409_CONFLICT
    link = "availability-drift"
    title = "Slot No Longer Available"
    log_level = logging.WARNING
    log_event = "scheduling.availability_drift"

    def __init__(self, slot_id: str, patient_id: str) -> None:
        super().__init__()
        self.slot_id = slot_id
        self.patient_id = patient_id

    def safe_detail(self) -> str:
        return (
            f"The slot '{self.slot_id}' was reserved by another patient. "
            "Refresh availability and try again."
        )

    def log_context(self) -> dict[str, object]:
        return {"slotId": self.slot_id, "patientId": self.patient_id}


class OverlappingModifierConflictError(IOPHADomainError):
    """Duration extension bled into an already-booked following appointment."""

    status_code = status.HTTP_409_CONFLICT
    link = "overlapping-modifier-conflict"
    title = "Appointment Overlaps Existing Booking"
    log_level = logging.WARNING
    log_event = "scheduling.overlapping_modifier_conflict"

    def __init__(
        self,
        slot_id: str,
        patient_id: str,
        conflicting_slot_id: str,
    ) -> None:
        super().__init__()
        self.slot_id = slot_id
        self.patient_id = patient_id
        self.conflicting_slot_id = conflicting_slot_id

    def safe_detail(self) -> str:
        return (
            f"Extending this appointment conflicts with slot "
            f"'{self.conflicting_slot_id}'. Reduce the duration or move the "
            "appointment."
        )

    def log_context(self) -> dict[str, object]:
        return {
            "slotId": self.slot_id,
            "patientId": self.patient_id,
            "conflictingSlotId": self.conflicting_slot_id,
        }


class WebSocketConnectionDropError(IOPHADomainError):
    """Realtime socket disconnected (e.g. network handoff) without backoff."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    link = "websocket-connection-drop"
    title = "Chat Connection Lost"
    log_level = logging.ERROR
    log_event = "chat.websocket_connection_drop"

    def __init__(self, session_id: str, patient_id: str) -> None:
        super().__init__()
        self.session_id = session_id
        self.patient_id = patient_id

    def safe_detail(self) -> str:
        return (
            "The realtime chat connection was lost. The client should "
            "reconnect with exponential backoff."
        )

    def log_context(self) -> dict[str, object]:
        return {"sessionId": self.session_id, "patientId": self.patient_id}


class OutOfOrderMessageDeliveryError(IOPHADomainError):
    """Async latency delivered a newer message before its predecessor."""

    status_code = status.HTTP_409_CONFLICT
    link = "out-of-order-message-delivery"
    title = "Messages Out of Order"
    log_level = logging.ERROR
    log_event = "chat.out_of_order_message_delivery"

    def __init__(
        self,
        session_id: str,
        message_id: str,
        expected_sequence: int,
        received_sequence: int,
    ) -> None:
        super().__init__()
        self.session_id = session_id
        self.message_id = message_id
        self.expected_sequence = expected_sequence
        self.received_sequence = received_sequence

    def safe_detail(self) -> str:
        return (
            "Incoming messages arrived out of chronological order. The client "
            "should re-sort by sequence before rendering."
        )

    def log_context(self) -> dict[str, object]:
        return {
            "sessionId": self.session_id,
            "messageId": self.message_id,
            "expectedSequence": self.expected_sequence,
            "receivedSequence": self.received_sequence,
        }


class UnreadNotificationInconsistencyError(IOPHADomainError):
    """Read receipt never reached the server; unread badge stays stale."""

    status_code = status.HTTP_409_CONFLICT
    link = "unread-notification-inconsistency"
    title = "Unread Count Out of Sync"
    log_level = logging.WARNING
    log_event = "chat.unread_notification_inconsistency"

    def __init__(self, session_id: str, patient_id: str, message_id: str) -> None:
        super().__init__()
        self.session_id = session_id
        self.patient_id = patient_id
        self.message_id = message_id

    def safe_detail(self) -> str:
        return (
            "The read receipt was not acknowledged by the server. The unread "
            "badge will resync on the next refresh."
        )

    def log_context(self) -> dict[str, object]:
        return {
            "sessionId": self.session_id,
            "patientId": self.patient_id,
            "messageId": self.message_id,
        }


class AttachmentPayloadTooLargeError(IOPHADomainError):
    """Uploaded chat attachment exceeded the max multipart body size (413)."""

    status_code = status.HTTP_413_CONTENT_TOO_LARGE
    link = "payload-too-large"
    title = "Attachment Too Large"
    log_level = logging.WARNING
    log_event = "chat.attachment_payload_too_large"

    def __init__(
        self,
        session_id: str,
        patient_id: str,
        max_size_bytes: int,
        actual_size_bytes: int,
    ) -> None:
        super().__init__()
        self.session_id = session_id
        self.patient_id = patient_id
        self.max_size_bytes = max_size_bytes
        self.actual_size_bytes = actual_size_bytes

    def safe_detail(self) -> str:
        return (
            "The uploaded attachment exceeded the maximum allowed size. "
            "Compress or split the file and try again."
        )

    def log_context(self) -> dict[str, object]:
        return {
            "sessionId": self.session_id,
            "patientId": self.patient_id,
            "maxSizeBytes": self.max_size_bytes,
            "actualSizeBytes": self.actual_size_bytes,
        }


class ExternalCalendarSyncDisconnectedError(IOPHADomainError):
    """Provider OAuth token expired/revoked; calendar sync is broken."""

    status_code = status.HTTP_502_BAD_GATEWAY
    link = "external-calendar-sync-disconnect"
    title = "Calendar Sync Disconnected"
    log_level = logging.ERROR
    log_event = "integration.external_calendar_sync_disconnect"

    def __init__(self, provider_id: str, patient_id: str) -> None:
        super().__init__()
        self.provider_id = provider_id
        self.patient_id = patient_id

    def safe_detail(self) -> str:
        return (
            "The linked external calendar is disconnected. Re-authorize the "
            "calendar integration to resume sync."
        )

    def log_context(self) -> dict[str, object]:
        return {"providerId": self.provider_id, "patientId": self.patient_id}


class UpstreamWebhookFailureError(IOPHADomainError):
    """EHR/cancellation webhook failed; secondary ledger is out of sync."""

    status_code = status.HTTP_502_BAD_GATEWAY
    link = "upstream-webhook-failure"
    title = "Upstream System Not Notified"
    log_level = logging.ERROR
    log_event = "integration.upstream_webhook_failure"

    def __init__(
        self,
        appointment_id: str,
        patient_id: str,
        webhook_target: str,
    ) -> None:
        super().__init__()
        self.appointment_id = appointment_id
        self.patient_id = patient_id
        self.webhook_target = webhook_target

    def safe_detail(self) -> str:
        return (
            "The change was saved locally but the upstream system was not "
            "notified. It will be retried automatically."
        )

    def log_context(self) -> dict[str, object]:
        return {
            "appointmentId": self.appointment_id,
            "patientId": self.patient_id,
            "webhookTarget": self.webhook_target,
        }


class NotificationGatewayTimeoutError(IOPHADomainError):
    """SMS/push gateway (Twilio/FCM) timed out or hit a rate limit."""

    status_code = status.HTTP_504_GATEWAY_TIMEOUT
    link = "notification-gateway-timeout"
    title = "Notification Delivery Timed Out"
    log_level = logging.ERROR
    log_event = "integration.notification_gateway_timeout"

    def __init__(self, patient_id: str, channel: str) -> None:
        super().__init__()
        self.patient_id = patient_id
        self.channel = channel

    def safe_detail(self) -> str:
        return (
            "The notification could not be delivered. It will be retried and "
            "may arrive shortly."
        )

    def log_context(self) -> dict[str, object]:
        return {"patientId": self.patient_id, "channel": self.channel}


class InvalidViewTransitionError(IOPHADomainError):
    """Frontend/backend disagreed on the current booking/chat phase."""

    status_code = status.HTTP_409_CONFLICT
    link = "invalid-view-transition"
    title = "Invalid State Transition"
    log_level = logging.WARNING
    log_event = "state_machine.invalid_view_transition"

    def __init__(
        self,
        current_view: str,
        expected_view: str,
        provider_id: str,
    ) -> None:
        super().__init__()
        self.current_view = current_view
        self.expected_view = expected_view
        self.provider_id = provider_id

    def safe_detail(self) -> str:
        return (
            "The requested screen transition is not valid from the current "
            "state. Return to the previous step and try again."
        )

    def log_context(self) -> dict[str, object]:
        return {
            "currentView": self.current_view,
            "expectedView": self.expected_view,
            "providerId": self.provider_id,
        }


class ExpiredBookingSessionError(IOPHADomainError):
    """Temporary slot hold expired before the user submitted the booking."""

    status_code = status.HTTP_410_GONE
    link = "expired-booking-session"
    title = "Booking Session Expired"
    log_level = logging.WARNING
    log_event = "state_machine.expired_booking_session"

    def __init__(
        self,
        slot_id: str,
        patient_id: str,
        hold_duration_seconds: int,
    ) -> None:
        super().__init__()
        self.slot_id = slot_id
        self.patient_id = patient_id
        self.hold_duration_seconds = hold_duration_seconds

    def safe_detail(self) -> str:
        return (
            f"The held slot '{self.slot_id}' was released after the session "
            "timed out. Please start the booking flow again."
        )

    def log_context(self) -> dict[str, object]:
        return {
            "slotId": self.slot_id,
            "patientId": self.patient_id,
            "holdDurationSeconds": self.hold_duration_seconds,
        }


# Ordered registry of every known domain exception. Registered as a global
# FastAPI exception handler (see app/handlers.register_exception_handlers)
# and documented in docs/infra/TECHNICAL_DESIGN.md.
DOMAIN_EXCEPTIONS: tuple[type[IOPHADomainError], ...] = (
    RaceConditionDoubleBookingError,
    TimeZoneMismatchError,
    AvailabilityDriftError,
    OverlappingModifierConflictError,
    WebSocketConnectionDropError,
    OutOfOrderMessageDeliveryError,
    UnreadNotificationInconsistencyError,
    AttachmentPayloadTooLargeError,
    ExternalCalendarSyncDisconnectedError,
    UpstreamWebhookFailureError,
    NotificationGatewayTimeoutError,
    InvalidViewTransitionError,
    ExpiredBookingSessionError,
)
