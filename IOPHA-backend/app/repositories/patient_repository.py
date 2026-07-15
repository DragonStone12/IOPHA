import copy
from abc import ABC, abstractmethod

from app.exceptions import DuplicatePatientError
from app.schemas.patient.patient_demographics import PatientRecord


class PatientRepository(ABC):
    """Persistence boundary for patient intake records."""

    @abstractmethod
    def create(self, record: PatientRecord) -> PatientRecord:
        """Persist a new patient record, returning a copy isolated from the store."""

    @abstractmethod
    def get_by_id(self, patient_id: str) -> PatientRecord | None:
        """Return the patient with *patient_id*, or ``None`` if absent."""

    @abstractmethod
    def exists_by_ssn(self, ssn: str) -> bool:
        """Return ``True`` if any stored patient uses *ssn*."""


class InMemoryPatientRepository(PatientRepository):
    """Default no-database stand-in used until a real datastore is wired.

    Holds patient records in a process-local dict keyed by generated
    ``patient_id`` and maintains a secondary SSN index for O(1) duplicate
    detection, so the intake service can reject re-submissions without any
    external state. ``create`` performs the existence check and the write in a
    single method so concurrent submissions cannot both pass the check before
    either writes (the prior TOCTOU window between ``exists_by_ssn`` and
    ``create`` is closed). Both writes and reads return copies so callers
    cannot mutate the internal store through the returned objects.
    """

    def __init__(self) -> None:
        self._patients: dict[str, PatientRecord] = {}
        self._ssn_index: set[str] = set()

    def create(self, record: PatientRecord) -> PatientRecord:
        if record.ssn in self._ssn_index:
            raise DuplicatePatientError(record.ssn)
        # Store and return isolated copies so the caller cannot corrupt the
        # internal store by mutating the returned object.
        stored = copy.copy(record)
        self._patients[record.patient_id] = stored
        self._ssn_index.add(record.ssn)
        return copy.copy(stored)

    def get_by_id(self, patient_id: str) -> PatientRecord | None:
        record = self._patients.get(patient_id)
        return copy.copy(record) if record is not None else None

    def exists_by_ssn(self, ssn: str) -> bool:
        return ssn in self._ssn_index


__all__ = ["InMemoryPatientRepository", "PatientRepository"]
