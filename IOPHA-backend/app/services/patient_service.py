import logging
import uuid
from abc import ABC, abstractmethod

from app.exceptions import PatientNotFoundException
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient.patient_demographics import (
    AddressRecord,
    EmergencyContactRecord,
    PatientDemographicsSchema,
    PatientIntakeRequest,
    PatientRecord,
    map_record_to_demographics,
)

logger = logging.getLogger("iopha.backend")


def _generate_patient_id() -> str:
    """Mint an opaque, non-sequential patient identifier."""
    return f"pat-{uuid.uuid4().hex[:12]}"


class PatientIntakeService(ABC):
    """Capture and resolve patient demographic intake records."""

    @abstractmethod
    def submit_intake(self, payload: PatientIntakeRequest) -> PatientDemographicsSchema:
        """Validate, persist, and return the created patient demographics."""

    @abstractmethod
    def get_demographics(self, patient_id: str) -> PatientDemographicsSchema:
        """Return the demographics for *patient_id*."""


class InMemoryPatientIntakeService(PatientIntakeService):
    """No-backend stand-in that stores intake in an in-memory repository."""

    def __init__(self, repository: PatientRepository) -> None:
        self._repository = repository

    def submit_intake(self, payload: PatientIntakeRequest) -> PatientDemographicsSchema:
        # Duplicate detection is performed atomically inside the repository's
        # ``create`` (check + write in one call) so concurrent submissions with
        # the same SSN cannot both pass the guard before either writes.
        record = PatientRecord(
            patient_id=_generate_patient_id(),
            first_name=payload.firstName,
            last_name=payload.lastName,
            date_of_birth=payload.dateOfBirth,
            ssn=payload.ssn,
            gender=payload.gender,
            address=AddressRecord(
                street=payload.address.street,
                city=payload.address.city,
                state=payload.address.state,
                postal_code=payload.address.postalCode,
                country=payload.address.country,
            ),
            phone_number=payload.phoneNumber,
            email=payload.email,
            emergency_contact=EmergencyContactRecord(
                name=payload.emergencyContact.name,
                relationship=payload.emergencyContact.relationship,
                phone_number=payload.emergencyContact.phoneNumber,
            ),
            preferred_communication=list(payload.preferredCommunication),
        )
        self._repository.create(record)
        logger.info("patient.intake_created")
        return map_record_to_demographics(record)

    def get_demographics(self, patient_id: str) -> PatientDemographicsSchema:
        record = self._repository.get_by_id(patient_id)
        if record is None:
            raise PatientNotFoundException(patient_id)
        logger.info("patient.retrieved")
        return map_record_to_demographics(record)


__all__ = [
    "InMemoryPatientIntakeService",
    "PatientIntakeService",
]
