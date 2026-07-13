import pytest
from pydantic import ValidationError

from app.schemas.find_doctor import FindDoctorResponseDataSchema, ProviderSearchRequest
from app.schemas.provider.provider_schema import ProviderSchema
from app.schemas.workflows.follow_up_action import FollowUpActionSchema


def test_provider_search_request_valid() -> None:
    payload = ProviderSearchRequest(queryText="Cardiologist")
    assert payload.queryText == "Cardiologist"


def test_provider_search_request_rejects_empty_string() -> None:
    with pytest.raises(ValidationError):
        ProviderSearchRequest(queryText="")


def test_find_doctor_response_schema_valid() -> None:
    response = FindDoctorResponseDataSchema(
        summaryText="Found 1 doctor near you.",
        providers=[
            ProviderSchema(
                id="doc-77",
                name="Dr. Sam",
                specialty="General",
                distance="1.2 miles",
                rating=5.0,
                reviewCount=10,
                nextAvailable="Tomorrow",
                imageUrl="/static/img.png",
                facility=None,
            )
        ],
        followUpActions=[
            FollowUpActionSchema(
                label="Book Now",
                actionType="BOOK_PROVIDER",
                providerId="doc-77",
            )
        ],
    )
    assert response.summaryText == "Found 1 doctor near you."
    assert len(response.providers) == 1
    assert response.providers[0].id == "doc-77"
    assert len(response.followUpActions) == 1
    assert response.followUpActions[0].actionType == "BOOK_PROVIDER"


def test_find_doctor_response_schema_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        FindDoctorResponseDataSchema(
            summaryText="Found doctors.",
            providers=[],
            followUpActions=[],
            unknownField="not allowed",  # type: ignore[call-arg]
        )


def test_follow_up_action_schema_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        FollowUpActionSchema(
            label="Book Now",
            actionType="BOOK_PROVIDER",
            providerId="doc-77",
            extraField="not allowed",  # type: ignore[call-arg]
        )
