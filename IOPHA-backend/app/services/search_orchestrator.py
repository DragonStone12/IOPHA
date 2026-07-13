from abc import ABC, abstractmethod

from app.schemas.find_doctor import FindDoctorResponseDataSchema


class SearchOrchestrator(ABC):
    """Abstraction over the provider discovery aggregation pipeline.

    Tests override the concrete implementation via
    ``app.dependency_overrides`` to inject deterministic doubles without
    touching any live search backend.
    """

    @abstractmethod
    def execute_query(self, query_string: str) -> FindDoctorResponseDataSchema:
        """Run the discovery pipeline for *query_string* and return the
        compound response payload."""


class InMemorySearchOrchestrator(SearchOrchestrator):
    """Default no-backend stand-in used until a real discovery microservice
    is wired."""

    def execute_query(self, query_string: str) -> FindDoctorResponseDataSchema:
        return FindDoctorResponseDataSchema(
            summaryText="",
            providers=[],
            followUpActions=[],
        )
