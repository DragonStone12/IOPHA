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
        # Python logging merges `extra` kwargs into record.__dict__, not record.extra.
        # Setting record.extra directly would test a code path that never executes.
        record.__dict__["email"] = "admin@example.com"
        record.__dict__["phone"] = "555-123-4567"
        assert filt.filter(record) is True
        assert record.__dict__["email"] == "[EMAIL_REDACTED]"
        assert record.__dict__["phone"] == "[PHONE_REDACTED]"

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

    def test_scrubs_credit_card_in_message(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Card: 4111-1111-1111-1111",
            args=(),
            exc_info=None,
        )
        assert filt.filter(record) is True
        assert "[CARD_REDACTED]" in record.msg
        assert "4111-1111-1111-1111" not in record.msg

    def test_scrubs_ip_address_in_message(self) -> None:
        filt = PIISanitizerFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="From 192.168.1.1 accessed",
            args=(),
            exc_info=None,
        )
        assert filt.filter(record) is True
        assert "[IP_REDACTED]" in record.msg
        assert "192.168.1.1" not in record.msg


# ---------------------------------------------------------------------------
# PIISanitizationMiddleware tests
# ---------------------------------------------------------------------------


class TestPIISanitizationMiddleware:
    @pytest.fixture
    def app(self) -> FastAPI:
        app = FastAPI()
        app.add_middleware(PIISanitizationMiddleware)

        @app.get("/patients/{patient_id}")
        def get_patient(patient_id: str, request: Request) -> dict[str, Any]:
            return {
                "patient_id": patient_id,
                "sanitized_path": request.state.sanitized_path,
                "sanitized_query": dict(request.state.sanitized_query),
                "scope_path": request.scope["path"],
                "scope_query_string": request.scope["query_string"].decode("utf-8"),
            }

        @app.get("/directory")
        def directory(request: Request) -> dict[str, Any]:
            return {
                "sanitized_path": request.state.sanitized_path,
                "sanitized_query": dict(request.state.sanitized_query),
                "scope_path": request.scope["path"],
                "scope_query_string": request.scope["query_string"].decode("utf-8"),
            }

        @app.get("/providers/{provider_id}")
        def get_provider(provider_id: str, request: Request) -> dict[str, Any]:
            return {
                "provider_id": provider_id,
                "sanitized_path": request.state.sanitized_path,
                "scope_path": request.scope["path"],
                "scope_query_string": request.scope["query_string"].decode("utf-8"),
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
        assert data["scope_path"] == "/patients/:id"

    def test_path_normalization_patients_uuid(self, client: TestClient) -> None:
        response = client.get("/patients/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code == 200
        data = response.json()
        assert data["sanitized_path"] == "/patients/:id"
        assert data["scope_path"] == "/patients/:id"

    def test_path_normalization_providers(self, client: TestClient) -> None:
        response = client.get("/providers/999")
        assert response.status_code == 200
        data = response.json()
        assert data["sanitized_path"] == "/providers/:id"
        assert data["scope_path"] == "/providers/:id"

    def test_path_normalization_providers_slug(self, client: TestClient) -> None:
        response = client.get("/providers/dr-emily-chen")
        assert response.status_code == 200
        data = response.json()
        assert data["sanitized_path"] == "/providers/:id"
        assert data["scope_path"] == "/providers/:id"

    def test_plain_paths_unchanged(self, client: TestClient) -> None:
        response = client.get("/directory")
        assert response.status_code == 200
        data = response.json()
        assert data["sanitized_path"] == "/directory"
        assert data["scope_path"] == "/directory"

    def test_sensitive_query_redacted(self, client: TestClient) -> None:
        response = client.get("/directory?email=test@example.com&phone=555-123-4567")
        assert response.status_code == 200
        data = response.json()
        assert data["sanitized_query"]["email"] == "[REDACTED]"
        assert data["sanitized_query"]["phone"] == "[REDACTED]"
        assert "email=%5BREDACTED%5D" in data["scope_query_string"]
        assert "phone=%5BREDACTED%5D" in data["scope_query_string"]
        assert "test@example.com" not in data["scope_query_string"]
        assert "555-123-4567" not in data["scope_query_string"]

    def test_non_sensitive_query_preserved(self, client: TestClient) -> None:
        response = client.get("/directory?specialty=cardiology")
        assert response.status_code == 200
        data = response.json()
        assert data["sanitized_query"]["specialty"] == "cardiology"
        assert "specialty=cardiology" in data["scope_query_string"]

    def test_query_string_is_valid_url_encoded_bytes(self, client: TestClient) -> None:
        response = client.get("/directory?specialty=cardiology&limit=10")
        assert response.status_code == 200
        data = response.json()
        scope_qs = data["scope_query_string"]
        assert scope_qs == "specialty=cardiology&limit=10"

    def test_raw_path_rebuilt_when_present(self, client: TestClient) -> None:
        response = client.get("/patients/12345")
        assert response.status_code == 200
        data = response.json()
        assert data["scope_path"] == "/patients/:id"


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
        assert "[EMAIL_REDACTED]" in json_str
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
        assert "[PHONE_REDACTED]" in json_str
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
        assert "[SSN_REDACTED]" in json_str
        assert "123-45-6789" not in json_str

    def test_name_partially_masked(self) -> None:
        dto = PatientDTO(
            patient_id=1,
            name="John Doe",
            email="john.doe@example.com",
            phone="555-123-4567",
            medical_record_number="123-45-6789",
        )
        assert dto.model_dump()["name"] == "J*** D***"
        assert "John" not in dto.model_dump()["name"]

    def test_name_masked_in_serialized_output(self) -> None:
        dto = PatientDTO(
            patient_id=1,
            name="John Doe",
            email="john.doe@example.com",
            phone="555-123-4567",
            medical_record_number="123-45-6789",
        )
        json_str = dto.model_dump_json()
        # The full name must never leak in cleartext in the serialized response.
        assert "John Doe" not in json_str
        assert "John" not in json_str
        assert "Doe" not in json_str
        # The name field must be masked.
        assert '"name":"J*** D***"' in json_str

    def test_single_name_partially_masked(self) -> None:
        dto = PatientDTO(
            patient_id=1,
            name="Madonna",
            email="john.doe@example.com",
            phone="555-123-4567",
            medical_record_number="123-45-6789",
        )
        assert dto.model_dump()["name"] == "M***"

    def test_empty_name_preserved(self) -> None:
        dto = PatientDTO(
            patient_id=1,
            name="",
            email="john.doe@example.com",
            phone="555-123-4567",
            medical_record_number="123-45-6789",
        )
        assert dto.model_dump()["name"] == ""

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
        # Patient name is PHI: partially masked for UI usability, not cleartext.
        assert data["name"] == "J*** D***"

    def test_unstructured_mrn_fully_withheld(self) -> None:
        dto = PatientDTO(
            patient_id=1,
            name="John Doe",
            email="john.doe@example.com",
            phone="MRN-A123456",
            medical_record_number="MRN-A123456",
        )
        json_str = dto.model_dump_json()
        assert '"medical_record_number":"[REDACTED]"' in json_str
        assert "MRN-A123456" not in json_str
        assert '"phone":"[REDACTED]"' in json_str
        assert "MRN-A123456" not in json_str

    def test_unstructured_phone_fully_withheld(self) -> None:
        dto = PatientDTO(
            patient_id=1,
            name="John Doe",
            email="john.doe@example.com",
            phone="+1 (555) 123-4567",
            medical_record_number="123-45-6789",
        )
        json_str = dto.model_dump_json()
        assert '"phone":"[REDACTED]"' in json_str
        assert "+1 (555) 123-4567" not in json_str

    def test_already_redacted_email_fully_withheld(self) -> None:
        dto = PatientDTO(
            patient_id=1,
            name="John Doe",
            email="[EMAIL_REDACTED]",
            phone="555-123-4567",
            medical_record_number="123-45-6789",
        )
        json_str = dto.model_dump_json()
        assert '"email":"[REDACTED]"' in json_str
        assert "[EMAIL_REDACTED]" not in json_str


class TestChatMessageDTO:
    def test_content_redacted_on_serialization(self) -> None:
        dto = ChatMessageDTO(
            message_id="msg-1",
            user_id=42,
            content="My email is john.doe@example.com",
            timestamp="2026-07-07T00:00:00Z",
        )
        json_str = dto.model_dump_json()
        # Update to match the specific redaction tag
        assert "[EMAIL_REDACTED]" in json_str
        assert "john.doe@example.com" not in json_str

    def test_content_credit_card_redacted(self) -> None:
        dto = ChatMessageDTO(
            message_id="msg-1",
            user_id=42,
            content="My card is 4111-1111-1111-1111",
            timestamp="2026-07-07T00:00:00Z",
        )
        json_str = dto.model_dump_json()
        assert "[CARD_REDACTED]" in json_str
        assert "4111-1111-1111-1111" not in json_str

    def test_content_ip_address_redacted(self) -> None:
        dto = ChatMessageDTO(
            message_id="msg-1",
            user_id=42,
            content="Server 192.168.1.1 is down",
            timestamp="2026-07-07T00:00:00Z",
        )
        json_str = dto.model_dump_json()
        assert "[IP_REDACTED]" in json_str
        assert "192.168.1.1" not in json_str

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
        # The content should now be preserved, not redacted
        assert data["content"] == "hello world"

    def test_mixed_pii_and_non_pii_preserved(self) -> None:
        dto = ChatMessageDTO(
            message_id="msg-1",
            user_id=42,
            content="hello email@example.com world",
            timestamp="2026-07-07T00:00:00Z",
        )
        data = dto.model_dump()
        assert data["content"] == "hello [EMAIL_REDACTED] world"


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
        # The non-PII part of the message should be echoed back
        assert data["content"] == "Call me at [PHONE_REDACTED]"
        assert "555-123-4567" not in data["content"]

    def test_message_requires_body(self) -> None:
        client = TestClient(main_app)
        response = client.post("/chat/message", json={})
        assert response.status_code == 422
