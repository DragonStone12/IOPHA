from app.exceptions import ProviderNotFoundException
from app.repositories.provider_repository import ProviderRepository
from app.schemas import PhysicianSchema, map_provider_to_physician


class ProviderService:
    """Business logic for the physician/provider scheduling domain.

    Translates repository lookups into normalized frontend contracts and
    raises structured domain exceptions when a resource is out of bounds.
    """

    def __init__(self, repository: ProviderRepository) -> None:
        self._repository = repository

    def get_physician(self, provider_id: str) -> PhysicianSchema:
        """Resolve and normalize a single physician entity by provider id.

        Raises ``ProviderNotFoundException`` when the underlying record is
        missing so the global handler can emit an RFC-7807 problem payload.
        """
        record = self._repository.find_by_id(provider_id)
        if record is None:
            raise ProviderNotFoundException(provider_id)
        return map_provider_to_physician(record)
