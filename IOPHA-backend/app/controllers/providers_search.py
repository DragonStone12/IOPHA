from fastapi import APIRouter, Depends

from app.dependencies import get_search_orchestrator
from app.schemas.find_doctor import FindDoctorResponseDataSchema, ProviderSearchRequest
from app.services.search_orchestrator import SearchOrchestrator


class SearchController:
    """HTTP surface for the provider discovery / find-doctor resource.

    The controller is kept free of persistence and business rules; it only
    adapts the orchestrator result into the frontend-aligned contract and
    leaves domain faults to the global handlers.
    """

    def __init__(self, orchestrator: SearchOrchestrator) -> None:
        self._orchestrator = orchestrator

    def search(self, payload: ProviderSearchRequest) -> FindDoctorResponseDataSchema:
        """Execute the discovery pipeline for the supplied query text."""
        return self._orchestrator.execute_query(payload.queryText)


def get_search_controller(
    orchestrator: SearchOrchestrator = Depends(get_search_orchestrator),  # noqa: B008
) -> SearchController:
    """Per-request factory that wires the orchestrator into the controller."""
    return SearchController(orchestrator)


router = APIRouter(prefix="/api/providers", tags=["providers-search"])


@router.post(
    "/search",
    response_model=FindDoctorResponseDataSchema,
    summary="Search for providers matching a natural language query",
    responses={
        200: {
            "description": ("Discovery result with providers and follow-up actions."),
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/FindDoctorResponseDataSchema"
                    }
                }
            },
        },
    },
)
def search_providers(
    payload: ProviderSearchRequest,
    controller: SearchController = Depends(get_search_controller),  # noqa: B008
) -> FindDoctorResponseDataSchema:
    """Run a provider discovery query and return a structured result.

    The response includes a natural-language ``summaryText``, a list of
    matching ``ProviderSchema`` records, and a list of ``FollowUpActionSchema``
    chips for client-side funnel routing.
    """
    return controller.search(payload)


__all__ = ["SearchController", "router"]
