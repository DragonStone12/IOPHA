from fastapi import APIRouter, Depends, status

from app.dependencies import get_booking_service
from app.schemas.booking import BookingRequestSchema, BookingResponseSchema
from app.services.booking_service import BookingService


class BookingController:
    """HTTP surface for the aggregate booking writer endpoint.

    The controller stays free of persistence and business rules; it only
    adapts the validated request into the service call and returns the
    frontend-aligned response contract.
    """

    def __init__(self, service: BookingService) -> None:
        self._service = service

    def create_booking(self, payload: BookingRequestSchema) -> BookingResponseSchema:
        """Process a transaction attempt and return structured summary metrics."""
        return self._service.create_booking(
            provider_id=payload.providerId,
            slot_id=payload.slotId,
            patient_data=payload.patientData,
        )


def get_booking_controller(
    service: BookingService = Depends(get_booking_service),  # noqa: B008
) -> BookingController:
    """Per-request factory wiring the booking service into the controller."""
    return BookingController(service)


router = APIRouter(prefix="/api/bookings", tags=["bookings"])


@router.post(
    "",
    response_model=BookingResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new booking",
    responses={
        201: {
            "description": "Booking created successfully.",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/BookingResponseSchema"}
                }
            },
        },
        400: {
            "description": "Invalid time slot format (InvalidTimeSlotFormatException)",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                }
            },
        },
        404: {
            "description": "Provider record was not found (ProviderNotFoundException)",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                }
            },
        },
        409: {
            "description": (
                "Time slot unavailable or schedule lock conflict "
                "(TimeSlotUnavailableException or ScheduleLockConflictException)"
            ),
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                }
            },
        },
        422: {
            "description": "Request payload validation failed (RequestValidationError)",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                }
            },
        },
    },
)
def create_booking(
    payload: BookingRequestSchema,
    controller: BookingController = Depends(get_booking_controller),  # noqa: B008
) -> BookingResponseSchema:
    """Commit a complete booking block backed by patient data validation.

    The nested :class:`PatientDataSchema` enforces strict PII/PHI rules at the
    API boundary before the booking service attempts to reserve the slot and
    persist the record.
    """
    return controller.create_booking(payload)


__all__ = ["BookingController", "router"]
