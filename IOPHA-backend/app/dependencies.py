from app.repositories.calendar_repository import (
    CalendarRepository,
    InMemoryCalendarRepository,
)
from app.repositories.provider_repository import (
    InMemoryProviderRepository,
    ProviderRepository,
)
from app.repositories.tips_repository import (
    InMemoryTipsRepository,
    TipsRepository,
)


def get_provider_repository() -> ProviderRepository:
    """FastAPI dependency factory yielding the active provider repository.

    Tests override this via ``app.dependency_overrides`` to inject an in-memory
    double without touching any live datastore.
    """
    return InMemoryProviderRepository()


def get_calendar_repository() -> CalendarRepository:
    """FastAPI dependency factory yielding the active calendar repository.

    Tests override this via ``app.dependency_overrides`` to inject a fault-
    injectable mock without touching any live calendar backend.
    """
    return InMemoryCalendarRepository()


def get_tips_repository() -> TipsRepository:
    """FastAPI dependency factory yielding the active tips repository.

    Tests override this via ``app.dependency_overrides`` to inject an in-memory
    (or fault-injectable) double without touching any live datastore.
    """
    return InMemoryTipsRepository()
