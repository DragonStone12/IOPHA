from app.exceptions.domain_errors import SearchAggregatorTimeoutError
from app.schemas.find_doctor import FindDoctorResponseDataSchema
from app.schemas.provider.provider_schema import ProviderSchema
from app.schemas.workflows.follow_up_action import FollowUpActionSchema
from app.services.search_orchestrator import SearchOrchestrator


class MockSearchOrchestrator(SearchOrchestrator):
    """Fault-injectable search double for integration tests."""

    def __init__(self, timeout_query: str = "timeout-trigger") -> None:
        self._timeout_query = timeout_query

    def execute_query(self, query_string: str) -> FindDoctorResponseDataSchema:
        if query_string == self._timeout_query:
            raise SearchAggregatorTimeoutError(query_string)
        return FindDoctorResponseDataSchema(
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
