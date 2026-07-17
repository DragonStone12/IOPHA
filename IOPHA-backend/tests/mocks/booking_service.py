from datetime import date

from app.schemas.booking import BookingResponseSchema, BookingSummarySchema
from app.schemas.patient.patient_data import PatientDataSchema
from app.schemas.physician.physician_schema import PhysicianSchema
from app.services.booking_service import BookingService


class MockBookingService(BookingService):
    """Fault-injectable booking service for isolated tests.

    Implements the :class:`BookingService` interface with configurable
    success/failure paths so tests can exercise the booking endpoint without
    touching any external calendar or booking backend.
    """

    def __init__(
        self,
        booking_id: str = "bk-test-123",
        raise_on_create: Exception | None = None,
    ) -> None:
        self._booking_id = booking_id
        self._raise_on_create = raise_on_create

    def create_booking(
        self,
        provider_id: str,
        slot_id: str,
        patient_data: PatientDataSchema,
    ) -> BookingResponseSchema:
        if self._raise_on_create is not None:
            raise self._raise_on_create

        physician = PhysicianSchema(
            id=provider_id,
            name="Dr. Test",
            specialty="General",
            distance="1.0 mi",
            rating=5.0,
            reviewCount=10,
            nextAvailable="Today",
            imageUrl=None,
            facility=None,
        )
        summary = BookingSummarySchema(
            physician=physician,
            date=date(2024, 1, 15),
            time="09:00 AM",
        )
        return BookingResponseSchema(bookingId=self._booking_id, summary=summary)
