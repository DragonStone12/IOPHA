from fastapi import Depends

from app.repositories.calendar_repository import (
    CalendarRepository,
    InMemoryCalendarRepository,
)
from app.repositories.patient_repository import (
    InMemoryPatientRepository,
    PatientRepository,
)
from app.repositories.provider_repository import (
    InMemoryProviderRepository,
    ProviderRepository,
)
from app.repositories.tips_repository import (
    InMemoryTipsRepository,
    TipsRepository,
)
from app.services.nutrition_service import (
    InMemoryNutritionCalculator,
    NutritionCalculator,
)
from app.services.patient_service import (
    InMemoryPatientIntakeService,
    PatientIntakeService,
)
from app.services.search_orchestrator import (
    InMemorySearchOrchestrator,
    SearchOrchestrator,
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


def get_search_orchestrator() -> SearchOrchestrator:
    """FastAPI dependency factory yielding the active search orchestrator.

    Tests override this via ``app.dependency_overrides`` to inject a fault-
    injectable double without touching any live discovery backend.
    """
    return InMemorySearchOrchestrator()


def get_nutrition_calculator() -> NutritionCalculator:
    """FastAPI dependency factory yielding the active nutrition calculator.

    Tests override this via ``app.dependency_overrides`` to inject a fault-
    injectable double without touching any live nutrition backend.
    """
    return InMemoryNutritionCalculator()


# A single shared in-memory store for the process. FastAPI resolves
# ``Depends(get_patient_repository)`` once per request, so returning a fresh
# ``InMemoryPatientRepository()`` here would discard state between requests.
# The store is intentionally shared so a patient created by ``POST /intake``
# is retrievable by a later ``GET /{patient_id}``. Tests override this
# dependency via ``app.dependency_overrides`` to inject their own store.
_default_patient_repository = InMemoryPatientRepository()


def get_patient_repository() -> PatientRepository:
    """FastAPI dependency factory yielding the active patient repository.

    Tests override this via ``app.dependency_overrides`` to inject an in-memory
    double without touching any live datastore.
    """
    return _default_patient_repository


def get_patient_intake_service(
    repository: PatientRepository = Depends(get_patient_repository),  # noqa: B008
) -> PatientIntakeService:
    """FastAPI dependency factory yielding the active patient intake service.

    Wires the patient repository into the service. Tests override
    ``get_patient_repository`` (or this factory) via ``app.dependency_overrides``
    to inject an in-memory double without touching any live backend.
    """
    return InMemoryPatientIntakeService(repository)
