from fastapi import APIRouter, Depends

from app.dependencies import get_provider_repository
from app.repositories.provider_repository import ProviderRepository
from app.schemas import PhysicianSchema
from app.services.provider_service import ProviderService


class ProviderController:
    """HTTP surface for the physician/provider scheduling resource.

    The controller is kept free of persistence and business rules; it only
    adapts the service result into the frontend-aligned contract and leaves
    domain faults (e.g. ``ProviderNotFoundException``) to the global handlers.
    """

    def __init__(self, service: ProviderService) -> None:
        self._service = service

    def retrieve(self, provider_id: str) -> PhysicianSchema:
        """Resolve and normalize a single physician entity by provider id."""
        return self._service.get_physician(provider_id)


def get_provider_controller(
    repository: ProviderRepository = Depends(get_provider_repository),  # noqa: B008
) -> ProviderController:
    """Per-request factory that wires the repository into the controller."""
    return ProviderController(ProviderService(repository))


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/{provider_id}", response_model=PhysicianSchema)
def get_provider(
    provider_id: str,
    controller: ProviderController = Depends(get_provider_controller),  # noqa: B008
) -> PhysicianSchema:
    return controller.retrieve(provider_id)
