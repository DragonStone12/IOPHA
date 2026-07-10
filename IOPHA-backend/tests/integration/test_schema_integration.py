"""Integration tests for schema mapping and serialization contracts.

These tests verify that internal domain records correctly project into the
external API schemas, and that all schemas accept/reject the expected
payloads. They sit between unit tests (which test single mappers/models in
isolation) and full end-to-end tests (which exercise the HTTP layer).
"""

import pytest
from pydantic import ValidationError

from app.schemas.physician.physician_schema import PhysicianSchema
from app.schemas.problem.problem_detail import ProblemDetail
from app.schemas.provider.mappers import map_provider_to_physician
from app.schemas.provider.provider_record import ProviderRecord
from app.schemas.provider.provider_schema import ProviderSchema


class TestProviderRecordToPhysicianSchemaMapping:
    """Verify the internal-to-external provider mapping contract."""

    @pytest.fixture
    def internal_record(self) -> ProviderRecord:
        return ProviderRecord(
            id="prov-123",
            name="Dr. Jane Doe",
            specialty="Cardiology",
            distance="2.4 mi",
            rating=4.8,
            reviewCount=124,
            nextAvailable="Today",
            imageUrl="https://example.com/jane.jpg",
            facility="Main Hospital",
            db_primary_key=999,
        )

    def test_maps_all_exposed_fields(self, internal_record: ProviderRecord) -> None:
        result = map_provider_to_physician(internal_record)
        assert result.id == "prov-123"
        assert result.name == "Dr. Jane Doe"
        assert result.specialty == "Cardiology"
        assert result.distance == "2.4 mi"
        assert result.rating == 4.8
        assert result.reviewCount == 124
        assert result.nextAvailable == "Today"
        assert result.imageUrl == "https://example.com/jane.jpg"
        assert result.facility == "Main Hospital"

    def test_db_primary_key_is_stripped(self, internal_record: ProviderRecord) -> None:
        result = map_provider_to_physician(internal_record)
        assert not hasattr(result, "db_primary_key")

    def test_serializes_to_json_without_errors(
        self, internal_record: ProviderRecord
    ) -> None:
        result = map_provider_to_physician(internal_record)
        payload = result.model_dump()
        assert payload["id"] == "prov-123"
        assert "db_primary_key" not in payload


class TestPhysicianSchemaValidation:
    """Verify PhysicianSchema enforces the external contract."""

    def test_accepts_minimal_valid_payload(self) -> None:
        schema = PhysicianSchema(
            id="p-1",
            name="Dr. Smith",
            specialty="General",
            distance="1.0 mi",
            rating=5.0,
            reviewCount=10,
            nextAvailable="Tomorrow",
        )
        assert schema.id == "p-1"

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            PhysicianSchema(
                id="p-1",
                name="Dr. Smith",
                specialty="General",
                distance="1.0 mi",
                rating=5.0,
                reviewCount=10,
                nextAvailable="Tomorrow",
                db_primary_key=1,
            )

    def test_rejects_missing_required_field(self) -> None:
        with pytest.raises(ValidationError):
            PhysicianSchema(
                id="p-1",
                name="Dr. Smith",
                specialty="General",
                distance="1.0 mi",
                rating=5.0,
                # reviewCount missing
                nextAvailable="Tomorrow",
            )


class TestProviderSchemaValidation:
    """Verify ProviderSchema enforces its contract."""

    def test_accepts_valid_payload(self) -> None:
        schema = ProviderSchema(
            id="prov-1",
            name="Clinic A",
            specialty="Dermatology",
            distance="3.2 mi",
            rating=4.5,
            reviewCount=89,
            nextAvailable="Next Week",
            imageUrl="https://example.com/clinic.jpg",
            facility="Downtown Clinic",
        )
        assert schema.facility == "Downtown Clinic"

    def test_image_url_and_facility_are_optional(self) -> None:
        schema = ProviderSchema(
            id="prov-2",
            name="Clinic B",
            specialty="Neurology",
            distance="5.0 mi",
            rating=4.2,
            reviewCount=45,
            nextAvailable="Next Month",
        )
        assert schema.imageUrl is None
        assert schema.facility is None


class TestProblemDetailSchemaValidation:
    """Verify ProblemDetail accepts/denies expected payloads."""

    def test_minimal_valid_problem_detail(self) -> None:
        problem = ProblemDetail(
            title="Not Found",
            status=404,
            detail="The requested resource was not found.",
            instance="/api/providers/missing",
            help_url="https://example.com/runbook#provider-not-found-error",
        )
        assert problem.status == 404
        assert "Not Found" in problem.title

    def test_errors_field_defaults_to_none(self) -> None:
        problem = ProblemDetail(
            title="Validation Error",
            status=422,
            detail="Input validation failed.",
            instance="/api/providers",
            help_url="https://example.com/runbook#validation-error",
        )
        assert problem.errors is None

    def test_accepts_optional_errors_array(self) -> None:
        problem = ProblemDetail(
            title="Validation Error",
            status=422,
            detail="Input validation failed.",
            instance="/api/providers",
            help_url="https://example.com/runbook#validation-error",
            errors=[
                {
                    "loc": ["body", "name"],
                    "msg": "required",
                    "type": "value_error.missing",
                }
            ],
        )
        assert problem.errors is not None
        assert len(problem.errors) == 1
        assert problem.errors[0]["loc"] == ["body", "name"]

    def test_extra_fields_are_allowed(self) -> None:
        problem = ProblemDetail(
            title="Error",
            status=400,
            detail="Bad request.",
            instance="/api/test",
            help_url="https://example.com/runbook",
            custom_field="allowed",
        )
        assert problem.custom_field == "allowed"  # type: ignore[attr-defined]
