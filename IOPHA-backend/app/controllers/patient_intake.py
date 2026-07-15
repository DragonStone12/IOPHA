import logging

from fastapi import APIRouter, Depends, status

from app.dependencies import get_patient_intake_service
from app.schemas.patient.patient_demographics import (
    PatientDemographicsSchema,
    PatientIntakeRequest,
)
from app.services.patient_service import PatientIntakeService

logger = logging.getLogger("iopha.backend")


class PatientIntakeController:
    """HTTP surface for the patient demographics intake resource.

    The controller is kept free of business rules; it only adapts the service
    result into the frontend-aligned contract and delegates persistence and
    validation to the service layer.
    """

    def __init__(self, service: PatientIntakeService) -> None:
        self._service = service

    def submit(self, payload: PatientIntakeRequest) -> PatientDemographicsSchema:
        """Capture and return the created patient demographics."""
        return self._service.submit_intake(payload)

    def get_by_id(self, patient_id: str) -> PatientDemographicsSchema:
        """Resolve the demographics for *patient_id*."""
        return self._service.get_demographics(patient_id)


def get_patient_intake_controller(
    service: PatientIntakeService = Depends(get_patient_intake_service),  # noqa: B008
) -> PatientIntakeController:
    """Per-request factory that wires the intake service into the controller."""
    return PatientIntakeController(service)


router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.post(
    "/intake",
    response_model=PatientDemographicsSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Submit patient demographics intake",
    responses={
        201: {
            "description": "Created patient demographics record.",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/PatientDemographicsSchema"}
                }
            },
        },
    },
)
def submit_patient_intake(
    payload: PatientIntakeRequest,
    controller: PatientIntakeController = Depends(get_patient_intake_controller),  # noqa: B008
) -> PatientDemographicsSchema:
    """Capture a new patient demographics intake.

    The payload is validated against :class:`PatientIntakeRequest` (bounded,
    PHI-aware rules) before persistence. A duplicate social security number is
    rejected with a 409 ``DuplicatePatientError`` problem. The social security
    number is never echoed back; the response carries a generated
    ``patientId`` instead.
    """
    return controller.submit(payload)


@router.get(
    "/{patient_id}",
    response_model=PatientDemographicsSchema,
    summary="Retrieve patient demographics",
    responses={
        200: {
            "description": "Resolved patient demographics.",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/PatientDemographicsSchema"}
                }
            },
        },
    },
)
def get_patient_demographics(
    patient_id: str,
    controller: PatientIntakeController = Depends(get_patient_intake_controller),  # noqa: B008
) -> PatientDemographicsSchema:
    """Return the demographics for *patient_id*.

    A missing record resolves to a 404 ``PatientNotFoundException`` problem.
    """
    return controller.get_by_id(patient_id)


__all__ = ["PatientIntakeController", "router"]
