import logging

from app.schemas.patient.patient_data import PatientDataSchema

logger = logging.getLogger("iopha.backend")


class IntakeService:
    """Business logic for the patient intake profile pipeline.

    Validates inbound patient attributes and projects them into the
    frontend-aligned response contract. No persistence is performed by the
    default stand-in; a real repository can be wired behind the same ABC.
    """

    def submit_intake(self, payload: PatientDataSchema) -> dict:
        """Validate and ingest a patient intake profile.

        Raises :class:`IntakeProcessingException` when the payload violates
        business constraints after schema validation has passed.
        """
        raise NotImplementedError


class InMemoryIntakeService(IntakeService):
    """No-backend stand-in that accepts every valid intake payload.

    Used in production today and overridden in tests to inject fault
    scenarios (e.g. forced ``IntakeProcessingException``) without touching
    any live downstream service.
    """

    def submit_intake(self, payload: PatientDataSchema) -> dict:
        logger.info(
            "intake.submitted",
            extra={
                "extra_context": {
                    "path": "/api/patients/intake",
                }
            },
        )
        return {
            "status": "processed",
            "id": "pt-1122",
        }


__all__ = ["InMemoryIntakeService", "IntakeService"]
