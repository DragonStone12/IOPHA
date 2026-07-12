from fastapi import APIRouter, Depends, Query

from app.dependencies import get_tips_repository
from app.repositories.tips_repository import TipsRepository
from app.schemas.tip import TipSchema
from app.services.tips_service import TipsService


class TipsController:
    """HTTP surface for the dynamic booking tips / advice resource.

    The controller is kept free of persistence and business rules; it only
    adapts the service result into the frontend-aligned contract.
    """

    def __init__(self, service: TipsService) -> None:
        self._service = service

    def list_tips(self, limit: int | None = None) -> list[TipSchema]:
        """Resolve and normalize the active booking tips."""
        return self._service.list_tips(limit)


def get_tips_controller(
    repository: TipsRepository = Depends(get_tips_repository),  # noqa: B008
) -> TipsController:
    """Per-request factory that wires the tips repository into the controller."""
    return TipsController(TipsService(repository))


router = APIRouter(prefix="/api/v1/tips", tags=["tips"])


@router.get(
    "",
    response_model=list[TipSchema],
    summary="List active dynamic booking tips",
    responses={
        200: {
            "description": "Ordered list of active booking tips / advice cards.",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/TipSchema"},
                    }
                }
            },
        },
    },
)
def get_tips(
    limit: int | None = Query(
        default=None,
        ge=1,
        le=100,
        description="Optional cap on the number of tips returned.",
    ),
    controller: TipsController = Depends(get_tips_controller),  # noqa: B008
) -> list[TipSchema]:
    """Return the active dynamic booking tips for the assistant UI.

    Each tip carries an ordered ``number`` for card stacking, an actionable
    ``title`` headline, and an elaborated ``description`` body. The optional
    ``limit`` query parameter caps how many cards are returned.
    """
    return controller.list_tips(limit)


__all__ = ["TipsController", "router"]
