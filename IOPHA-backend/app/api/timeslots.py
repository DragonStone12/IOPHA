from fastapi import APIRouter, Depends

from app.dependencies import get_calendar_repository
from app.repositories.calendar_repository import CalendarRepository
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
    response_model=list[TimeSlotSchema],
    summary="List available time slots for a provider",
    responses={
        200: {
            "description": "List of available and booked time slots for the provider.",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/TimeSlotSchema"},
                    }
                }
            },
        }
    },
)
def get_provider_slots(
    provider_id: str,
    controller: TimeSlotController = Depends(get_timeslot_controller),  # noqa: B008
) -> list[TimeSlotSchema]:
    """Return the time-slot availability calendar for the given provider.

    Each slot carries a unique ``id`` (ISO date + civil time), the display
    ``time``/``label``, and an ``available`` flag the booking UI uses to
    enable or disable the slot button.
    """
    return controller.list_slots(provider_id)


__all__ = ["TimeSlotController", "router"]
