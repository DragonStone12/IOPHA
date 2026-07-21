import logging

from fastapi import APIRouter, Depends, status

from app.dependencies import get_intake_service
from app.schemas.patient.patient_data import PatientDataSchema
from app.services.intake_service import IntakeService

logger = logging.getLogger("iopha.backend")


class PatientController:
    """HTTP surface for the patient intake profile resource.

    The controller is kept free of persistence and business rules; it only
    adapts the service result into the frontend-aligned contract.
    """

    def __init__(self, service: IntakeService) -> None:
        self._service = service

    def submit_intake(self, payload: PatientDataSchema) -> dict:
        """Capture and return the processed intake profile."""
        return self._service.submit_intake(payload)


def get_patient_controller(
    service: IntakeService = Depends(get_intake_service),  # noqa: B008
) -> PatientController:
    """Per-request factory that wires the intake service into the controller."""
    return PatientController(service)


router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.post(
    "/intake",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Submit patient intake profile",
    responses={
        200: {
            "description": "Intake profile processed successfully.",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "id": {"type": "string"},
                        },
                    }
                }
            },
        },
        422: {
            "description": ("Intake processing failure (IntakeProcessingException)"),
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                }
            },
        },
    },
)
def submit_intake(
    payload: PatientDataSchema,
    controller: PatientController = Depends(get_patient_controller),  # noqa: B008
) -> dict:
    """Submit a patient intake profile for processing.

    The payload is validated against :class:`PatientDataSchema` (rigid,
    PHI-aware rules) before processing. A processing failure raises
    ``IntakeProcessingException``, which the global handler projects into
    an RFC-7807 ``ProblemDetail`` (422) with a ``help_url`` runbook link.
    """
    return controller.submit_intake(payload)


__all__ = ["PatientController", "router"]
