import logging
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_patient_repository
from app.main import app
from app.repositories.patient_repository import InMemoryPatientRepository
from app.schemas.patient.patient_demographics import PatientDemographicsSchema

LEAK_MARKERS = (
    "Traceback",
    "Exception(",
    "0x",
    "password",
    "secret",
    "Bearer ",
    "postgresql",
)


class _CaptureHandler(logging.Handler):
    def __init__(self, sink: list[logging.LogRecord]) -> None:
        super().__init__()
        self._sink = sink

    def emit(self, record: logging.LogRecord) -> None:
        self._sink.append(record)


@pytest.fixture
def log_records() -> Generator[list[logging.LogRecord], None, None]:
    records: list[logging.LogRecord] = []
    handler = _CaptureHandler(records)
    logger = logging.getLogger("iopha.backend")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        yield records
    finally:
        logger.removeHandler(handler)


@pytest.fixture(autouse=True)
def bind_patient_repo() -> Generator[None, None, None]:
    """Override the patient repository dependency with a single shared store.

    The lambda closes over one ``InMemoryPatientRepository`` instance so every
    request in the test reads/writes the same store (FastAPI resolves
    ``Depends`` per request, so a fresh instance per call would lose state).
    """
    repo = InMemoryPatientRepository()
    app.dependency_overrides[get_patient_repository] = lambda: repo
    try:
        yield
    finally:
        # Pop only the key this fixture set; never clear() the whole override
        # map (see TROUBLESHOOTING.md: Python Testing Anti-Patterns).
        app.dependency_overrides.pop(get_patient_repository, None)


def _valid_intake() -> dict:
    return {
        "firstName": "Jane",
        "lastName": "Doe",
        "dateOfBirth": "1990-05-14",
        "ssn": "123-45-6789",
        "gender": "Female",
        "address": {
            "street": "123 Main St",
            "city": "Dallas",
            "state": "TX",
            "postalCode": "75201",
            "country": "USA",
        },
        "phoneNumber": "+12145550123",
        "email": "jane.doe@example.com",
        "emergencyContact": {
            "name": "John Doe",
            "relationship": "Spouse",
            "phoneNumber": "+12145550987",
        },
        "preferredCommunication": ["Email", "SMS"],
    }


def test_patient_intake_happy_path(
    log_records: list[logging.LogRecord],
) -> None:
    request_id = "22222222-2222-2222-2222-222222222222"
    with TestClient(app) as client:
        response = client.post(
            "/api/patients/intake",
            json=_valid_intake(),
            headers={"X-Request-ID": request_id},
        )
    assert response.status_code == 201
    body = response.json()
    assert body["firstName"] == "Jane"
    assert body["lastName"] == "Doe"
    assert body["dateOfBirth"] == "1990-05-14"
    assert body["patientId"].startswith("pat-")
    # SSN must never be echoed to the client.
    assert "ssn" not in body
    # Response must validate against the external DTO.
    PatientDemographicsSchema.model_validate(body)

    record = next(
        (r for r in log_records if r.getMessage() == "patient.intake_created"),
        None,
    )
    assert record is not None


def test_patient_intake_retrieve_by_id(
    log_records: list[logging.LogRecord],
) -> None:
    with TestClient(app) as client:
        created = client.post("/api/patients/intake", json=_valid_intake())
        patient_id = created.json()["patientId"]
        response = client.get(f"/api/patients/{patient_id}")
    assert response.status_code == 200
    assert response.json()["patientId"] == patient_id

    record = next(
        (r for r in log_records if r.getMessage() == "patient.retrieved"),
        None,
    )
    assert record is not None


def test_patient_intake_missing_fields_returns_422() -> None:
    payload = _valid_intake()
    del payload["ssn"]
    with TestClient(app) as client:
        response = client.post("/api/patients/intake", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["status"] == 422
    assert body["title"] == "Unprocessable Entity"
    assert body["instance"] == "/api/patients/intake"
    assert body["help_url"].endswith("#unprocessable-entity-error")
    assert body["help_url"].startswith(
        "https://github.com/DragonStone12/IOPHA/blob/main/docs/RUNBOOKS.md#"
    )
    for marker in LEAK_MARKERS:
        assert marker not in response.text


def test_patient_intake_rejects_unknown_field_422() -> None:
    payload = _valid_intake()
    payload["intakeSource"] = "web"
    with TestClient(app) as client:
        response = client.post("/api/patients/intake", json=payload)
    assert response.status_code == 422
    for marker in LEAK_MARKERS:
        assert marker not in response.text


# --- Isolated error-handling tests (RFC-7807 problem payloads) ---


def test_patient_not_found_returns_404(
    log_records: list[logging.LogRecord],
) -> None:
    request_id = "33333333-3333-3333-3333-333333333333"
    with TestClient(app) as client:
        response = client.get(
            "/api/patients/pat-missing",
            headers={"X-Request-ID": request_id},
        )
    assert response.status_code == 404
    body = response.json()
    assert body["status"] == 404
    assert body["title"] == "Patient Record Absent"
    assert body["instance"] == "/api/patients/pat-missing"
    assert body["help_url"].endswith("#patient-not-found-error")
    assert body["help_url"].startswith(
        "https://github.com/DragonStone12/IOPHA/blob/main/docs/RUNBOOKS.md#"
    )
    assert response.headers["X-Request-ID"] == request_id
    for marker in LEAK_MARKERS:
        assert marker not in response.text

    record = next(
        (r for r in log_records if r.getMessage() == "patient.not_found"),
        None,
    )
    assert record is not None
    ctx = getattr(record, "extra_context", {})
    assert ctx["requestId"] == response.headers["X-Request-ID"]
    assert ctx["path"] == "/api/patients/pat-missing"
    assert ctx["patientId"] == "pat-missing"


def test_duplicate_patient_returns_409(
    log_records: list[logging.LogRecord],
) -> None:
    request_id = "44444444-4444-4444-4444-444444444444"
    with TestClient(app) as client:
        first = client.post("/api/patients/intake", json=_valid_intake())
        assert first.status_code == 201
        response = client.post(
            "/api/patients/intake",
            json=_valid_intake(),
            headers={"X-Request-ID": request_id},
        )
    assert response.status_code == 409
    body = response.json()
    assert body["status"] == 409
    assert body["title"] == "Patient Record Already Exists"
    assert body["instance"] == "/api/patients/intake"
    assert body["help_url"].endswith("#duplicate-patient-error")
    assert body["help_url"].startswith(
        "https://github.com/DragonStone12/IOPHA/blob/main/docs/RUNBOOKS.md#"
    )
    assert response.headers["X-Request-ID"] == request_id
    # Neither the SSN nor any PHI may leak into the problem payload or logs.
    for marker in LEAK_MARKERS:
        assert marker not in response.text
    assert "123-45-6789" not in response.text

    record = next(
        (r for r in log_records if r.getMessage() == "patient.duplicate"),
        None,
    )
    assert record is not None
    ctx = getattr(record, "extra_context", {})
    assert ctx["requestId"] == response.headers["X-Request-ID"]
    assert ctx["path"] == "/api/patients/intake"
    assert ctx.get("duplicateDetected") is True
    assert "ssn" not in ctx
