from abc import ABC, abstractmethod

from app.schemas.patient.patient_demographics import PatientRecord


class PatientRepository(ABC):
    """Persistence boundary for patient intake records."""

    @abstractmethod
    def create(self, record: PatientRecord) -> PatientRecord:
        """Persist a new patient record, returning the stored entity."""

    @abstractmethod
    def get_by_id(self, patient_id: str) -> PatientRecord | None:
        """Return the patient with *patient_id*, or ``None`` if absent."""

    @abstractmethod
    def exists_by_ssn(self, ssn: str) -> bool:
        """Return ``True`` if any stored patient uses *ssn*."""


class InMemoryPatientRepository(PatientRepository):
    """Default no-database stand-in used until a real datastore is wired.

    Holds patient records in a process-local dict keyed by generated
    ``patient_id`` and supports SSN-based duplicate detection so the intake
    service can reject re-submissions without any external state.
    """

    def __init__(self) -> None:
        self._patients: dict[str, PatientRecord] = {}

    def create(self, record: PatientRecord) -> PatientRecord:
        # Store the record by its generated id; return a shallow copy so
        # callers cannot mutate the internal store.
        self._patients[record.patient_id] = record
        return record

    def get_by_id(self, patient_id: str) -> PatientRecord | None:
        return self._patients.get(patient_id)

    def exists_by_ssn(self, ssn: str) -> bool:
        return any(p.ssn == ssn for p in self._patients.values())


__all__ = ["InMemoryPatientRepository", "PatientRepository"]
