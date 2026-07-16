from abc import ABC, abstractmethod

from app.schemas import ProviderRecord


class ProviderRepository(ABC):
    """Persistence boundary for provider/physician directory lookups."""

    @abstractmethod
    def find_by_id(self, provider_id: str) -> ProviderRecord | None:
        """Return the internal record for ``provider_id`` or ``None`` if absent."""


class InMemoryProviderRepository(ProviderRepository):
    """Default no-database stand-in used until a real datastore is wired."""

    def __init__(self) -> None:
        self._store: dict[str, ProviderRecord] = {
            "prov-123": ProviderRecord(
                id="prov-123",
                name="Dr. Emily Chen, MD",
                specialty="Cardiology",
                distance="1.8 miles",
                rating=4.9,
                reviewCount=120,
                nextAvailable="Today, 3:30 PM",
                imageUrl="https://cdn.example.com/emily.jpg",
                facility="Northside Medical Center",
                db_primary_key=42,
            ),
        }

    def find_by_id(self, provider_id: str) -> ProviderRecord | None:
        return self._store.get(provider_id)
