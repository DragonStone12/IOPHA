from app.repositories.provider_repository import (
    InMemoryProviderRepository,
    ProviderRepository,
)


def get_provider_repository() -> ProviderRepository:
    """FastAPI dependency factory yielding the active provider repository.

    Tests override this via ``app.dependency_overrides`` to inject an in-memory
    double without touching any live datastore.
    """
    return InMemoryProviderRepository()
