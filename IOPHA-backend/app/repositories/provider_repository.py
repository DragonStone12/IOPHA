from abc import ABC, abstractmethod

from app.repositories.seed_data import seed_providers
from app.schemas import ProviderRecord


class ProviderRepository(ABC):
    """Persistence boundary for provider/physician directory lookups."""

    @abstractmethod
    def find_by_id(self, provider_id: str) -> ProviderRecord | None:
        """Return the internal record for ``provider_id`` or ``None`` if absent."""


class InMemoryProviderRepository(ProviderRepository):
    """Default no-database stand-in used until a real datastore is wired.

    Intentionally starts pre-populated with the shared seed providers from
    :mod:`app.repositories.seed_data` (the same records used by
    ``InMemoryCalendarRepository``) so the provider directory and booking
    endpoints work out of the box.
    """

    def __init__(self) -> None:
        self._store: dict[str, ProviderRecord] = seed_providers()

    def find_by_id(self, provider_id: str) -> ProviderRecord | None:
        return self._store.get(provider_id)
