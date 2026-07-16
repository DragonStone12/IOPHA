from datetime import date

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_calendar_repository
from app.repositories.calendar_repository import CalendarRepository
from app.schemas.booking import CalendarSlotsResponseSchema
from app.schemas.timeslot import TimeSlotSchema
from app.services.timeslot_service import TimeSlotService


class TimeSlotController:
    """HTTP surface for provider time-slot availability.

    The controller stays free of persistence and business rules; it only
    adapts the service result into the frontend-aligned contract.
    """

    def __init__(self, service: TimeSlotService) -> None:
        self._service = service

    def list_slots(self, provider_id: str) -> list[TimeSlotSchema]:
        """Resolve and normalize a provider's available time slots."""
        return self._service.get_slots(provider_id)

    def get_calendar_slots(
        self,
        provider_id: str,
        query_date: date,
    ) -> CalendarSlotsResponseSchema:
        """Resolve day-scoped calendar availability for a provider."""
        return self._service.get_calendar_slots_for_date(provider_id, query_date)

    def reserve_slot(self, provider_id: str, slot_id: str) -> dict[str, str]:
        """Reserve a slot on behalf of the patient."""
        self._service.reserve_slot(provider_id, slot_id)
        return {"status": "reserved", "slot_id": slot_id}


def get_timeslot_controller(
    repository: CalendarRepository = Depends(get_calendar_repository),  # noqa: B008
) -> TimeSlotController:
    """Per-request factory that wires the calendar repository into the controller."""
    return TimeSlotController(TimeSlotService(repository))


# Shares the provider prefix so the availability resource nests under the
# same provider entity exposed by the directory API.
router = APIRouter(prefix="/api/providers", tags=["time-slots"])


@router.get(
    "/{provider_id}/slots",
    response_model=CalendarSlotsResponseSchema,
    summary="List available time slots for a provider on a specific date",
    responses={
        200: {
            "description": (
                "Day-scoped map of available and booked time slots for the provider."
            ),
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/CalendarSlotsResponseSchema"
                    }
                }
            },
        },
        404: {
            "description": "Provider not found.",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                }
            },
        },
        422: {
            "description": "Invalid date query parameter.",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                }
            },
        },
    },
)
def get_provider_slots(
    provider_id: str,
    date: date = Query(..., description="Target query date formatted as YYYY-MM-DD"),  # noqa: B008
    controller: TimeSlotController = Depends(get_timeslot_controller),  # noqa: B008
) -> CalendarSlotsResponseSchema:
    """Return the day-scoped time-slot availability calendar for the provider.

    The response groups every calendar node for the requested ISO date so the
    booking UI can render the date header and slot grid from a single payload.
    """
    return controller.get_calendar_slots(provider_id, date)


@router.post(
    "/{provider_id}/slots/{slot_id}/reserve",
    summary="Reserve a specific time slot",
    responses={
        200: {
            "description": "Slot successfully reserved.",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "slot_id": {"type": "string"},
                        },
                    }
                }
            },
        },
        400: {
            "description": "Invalid time slot format.",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                }
            },
        },
        404: {
            "description": "Provider not found.",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                }
            },
        },
        409: {
            "description": "Time slot unavailable.",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                }
            },
        },
    },
)
def reserve_provider_slot(
    provider_id: str,
    slot_id: str,
    controller: TimeSlotController = Depends(get_timeslot_controller),  # noqa: B008
) -> dict[str, str]:
    """Reserve the identified slot for the current patient session."""
    return controller.reserve_slot(provider_id, slot_id)


__all__ = ["TimeSlotController", "router"]
