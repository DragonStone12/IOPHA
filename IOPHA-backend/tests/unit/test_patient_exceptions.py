from app.exceptions import DuplicatePatientError, PatientNotFoundException


class TestDuplicatePatientError:
    def test_status_and_link(self) -> None:
        exc = DuplicatePatientError("123-45-6789")
        assert exc.status_code == 409
        assert exc.link == "duplicate-patient-error"
        assert exc.title == "Patient Record Already Exists"

    def test_safe_detail_does_not_leak_ssn(self) -> None:
        exc = DuplicatePatientError("123-45-6789")
        detail = exc.safe_detail()
        assert "123-45-6789" not in detail
        assert "social security number" in detail

    def test_log_context_omits_ssn(self) -> None:
        exc = DuplicatePatientError("123-45-6789")
        ctx = exc.log_context()
        assert ctx.get("duplicateDetected") is True
        assert "ssn" not in ctx


class TestPatientNotFoundException:
    def test_status_and_link(self) -> None:
        exc = PatientNotFoundException("pat-abc123")
        assert exc.status_code == 404
        assert exc.link == "patient-not-found-error"
        assert exc.title == "Patient Record Absent"

    def test_safe_detail_includes_id(self) -> None:
        exc = PatientNotFoundException("pat-abc123")
        assert "pat-abc123" in exc.safe_detail()

    def test_log_context_includes_patient_id(self) -> None:
        exc = PatientNotFoundException("pat-abc123")
        assert exc.log_context()["patientId"] == "pat-abc123"
