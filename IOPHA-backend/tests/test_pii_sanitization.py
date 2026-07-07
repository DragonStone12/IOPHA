import logging
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.main import (
    ChatMessageDTO,
    PatientDTO,
    PIISanitizationMiddleware,
    PIISanitizerFilter,
)
from app.main import (
    app as main_app,
)

# ---------------------------------------------------------------------------
# PIISanitizerFilter tests
# ---------------------------------------------------------------------------


class TestPIISanitizerFilter:
    def test_scrubs_email_in_message(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Contact admin@example.com for help",
            args=(),
            exc_info=None,
        )
        assert filt.filter(record) is True
        assert "[EMAIL_REDACTED]" in record.msg
        assert "admin@example.com" not in record.msg

    def test_scrubs_phone_in_message(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Call 555-123-4567 now",
            args=(),
            exc_info=None,
        )
        assert filt.filter(record) is True
        assert "[PHONE_REDACTED]" in record.msg

    def test_scrubs_ssn_in_message(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="SSN: 123-45-6789",
            args=(),
            exc_info=None,
        )
        assert filt.filter(record) is True
        assert "[SSN_REDACTED]" in record.msg

    def test_scrubs_tuple_args(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User %s logged in",
            args=("admin@example.com",),
            exc_info=None,
        )
        assert filt.filter(record) is True
        sanitized = record.msg % record.args
        assert "[EMAIL_REDACTED]" in sanitized
        assert "admin@example.com" not in sanitized

    def test_scrubs_dict_args(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User %(email)s logged in",
            args={"email": "admin@example.com", "id": 1},
            exc_info=None,
        )
        assert filt.filter(record) is True
        sanitized = record.msg % record.args
        assert "[EMAIL_REDACTED]" in sanitized
        assert "admin@example.com" not in sanitized

    def test_scrubs_extra_dict(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Request processed",
            args=(),
            exc_info=None,
        )
        record.extra = {"email": "admin@example.com", "phone": "555-123-4567"}
        assert filt.filter(record) is True
        assert hasattr(record, "extra")
        assert record.extra["email"] == "[EMAIL_REDACTED]"
        assert record.extra["phone"] == "[PHONE_REDACTED]"

    def test_non_string_args_untouched(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Count %d",
            args=(42,),
            exc_info=None,
        )
        assert filt.filter(record) is True
        assert record.args == (42,)

    def test_multiple_pii_types_in_message(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Contact admin@example.com or 555-123-4567, SSN: 123-45-6789",
            args=(),
            exc_info=None,
        )
        assert filt.filter(record) is True
        assert "[EMAIL_REDACTED]" in record.msg
        assert "[PHONE_REDACTED]" in record.msg
        assert "[SSN_REDACTED]" in record.msg


# ---------------------------------------------------------------------------
# PIISanitizationMiddleware tests
# ---------------------------------------------------------------------------


class TestPIISanitizationMiddleware:
    @pytest.fixture
    def app(self) -> FastAPI:
        app = FastAPI()
        app.add_middleware(PIISanitizationMiddleware)

        @app.get("/patients/{patient_id}")
        def get_patient(patient_id: int, request: Request) -> dict[str, Any]:
            return {
                "patient_id": patient_id,
                "sanitized_path": request.state.sanitized_path,
                "sanitized_query": dict(request.state.sanitized_query),
            }

        @app.get("/directory")
        def directory(request: Request) -> dict[str, Any]:
            return {
                "sanitized_path": request.state.sanitized_path,
                "sanitized_query": dict(request.state.sanitized_query),
            }

        @app.get("/providers/{provider_id}")
        def get_provider(provider_id: int, request: Request) -> dict[str, Any]:
            return {
                "provider_id": provider_id,
                "sanitized_path": request.state.sanitized_path,
            }

        return app

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        return TestClient(app)

    def test_path_normalization_patients(self, client: TestClient) -> None:
        response = client.get("/patients/12345")
        assert response.status_code == 200
        data = response.json()
        assert data["sanitized_path"] == "/patients/:id"

    def test_path_normalization_providers(self, client: TestClient) -> None:
        response = client.get("/providers/999")
        assert response.status_code == 200
        data = response.json()
        assert data["sanitized_path"] == "/providers/:id"

    def test_plain_paths_unchanged(self, client: TestClient) -> None:
        response = client.get("/directory")
        assert response.status_code == 200
        data = response.json()
        assert data["sanitized_path"] == "/directory"

    def test_sensitive_query_redacted(self, client: TestClient) -> None:
        response = client.get("/directory?email=test@example.com&phone=555-123-4567")
        assert response.status_code == 200
        data = response.json()
        assert data["sanitized_query"]["email"] == "[REDACTED]"
        assert data["sanitized_query"]["phone"] == "[REDACTED]"

    def test_non_sensitive_query_preserved(self, client: TestClient) -> None:
        response = client.get("/directory?specialty=cardiology")
        assert response.status_code == 200
        data = response.json()
        assert data["sanitized_query"]["specialty"] == "cardiology"


# ---------------------------------------------------------------------------
# Pydantic DTO serialization tests
# ---------------------------------------------------------------------------


class TestPatientDTO:
    def test_email_redacted_on_serialization(self) -> None:
        dto = PatientDTO(
            patient_id=1,
            name="John Doe",
            email="john.doe@example.com",
            phone="555-123-4567",
            medical_record_number="123-45-6789",
        )
        json_str = dto.model_dump_json()
        assert "[REDACTED]" in json_str
        assert "john.doe@example.com" not in json_str

    def test_phone_redacted_on_serialization(self) -> None:
        dto = PatientDTO(
            patient_id=1,
            name="John Doe",
            email="john.doe@example.com",
            phone="555-123-4567",
            medical_record_number="123-45-6789",
        )
        json_str = dto.model_dump_json()
        assert "[REDACTED]" in json_str
        assert "555-123-4567" not in json_str

    def test_medical_record_number_redacted(self) -> None:
        dto = PatientDTO(
            patient_id=1,
            name="John Doe",
            email="john.doe@example.com",
            phone="555-123-4567",
            medical_record_number="123-45-6789",
        )
        json_str = dto.model_dump_json()
        assert "[REDACTED]" in json_str
        assert "123-45-6789" not in json_str

    def test_non_pii_fields_preserved(self) -> None:
        dto = PatientDTO(
            patient_id=1,
            name="John Doe",
            email="john.doe@example.com",
            phone="555-123-4567",
            medical_record_number="123-45-6789",
        )
        data = dto.model_dump()
        assert data["patient_id"] == 1
        assert data["name"] == "John Doe"


class TestChatMessageDTO:
    def test_content_redacted_on_serialization(self) -> None:
        dto = ChatMessageDTO(
            message_id="msg-1",
            user_id=42,
            content="My email is john.doe@example.com",
            timestamp="2026-07-07T00:00:00Z",
        )
        json_str = dto.model_dump_json()
        assert "[REDACTED]" in json_str
        assert "john.doe@example.com" not in json_str

    def test_non_pii_fields_preserved(self) -> None:
        dto = ChatMessageDTO(
            message_id="msg-1",
            user_id=42,
            content="hello world",
            timestamp="2026-07-07T00:00:00Z",
        )
        data = dto.model_dump()
        assert data["message_id"] == "msg-1"
        assert data["user_id"] == 42
        assert data["content"] == "[REDACTED]"


class TestChatMessageEndpoint:
    def test_message_echoes_with_redacted_content(self) -> None:
        client = TestClient(main_app)
        payload = {
            "message_id": "msg-2",
            "user_id": 7,
            "content": "Call me at 555-123-4567",
            "timestamp": "2026-07-07T00:00:00Z",
        }
        response = client.post("/chat/message", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["message_id"] == "msg-2"
        assert data["user_id"] == 7
        assert data["content"] == "[REDACTED]"
        assert "555-123-4567" not in data["content"]

    def test_message_requires_body(self) -> None:
        client = TestClient(main_app)
        response = client.post("/chat/message", json={})
        assert response.status_code == 422
