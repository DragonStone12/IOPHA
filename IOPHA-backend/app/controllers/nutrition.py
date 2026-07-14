import logging

from fastapi import APIRouter, Depends

from app.dependencies import get_nutrition_calculator
from app.schemas.nutrition_response import (
    NutritionEvaluateRequest,
    NutritionResponseDataSchema,
)
from app.services.nutrition_service import NutritionCalculator

logger = logging.getLogger("iopha.backend")


class NutritionController:
    """HTTP surface for the nutrition response / advice resource.

    The controller is kept free of business rules; it only adapts the
    calculator result into the frontend-aligned contract.
    """

    def __init__(self, calculator: NutritionCalculator) -> None:
        self._calculator = calculator

    def evaluate(self, profile_id: str) -> NutritionResponseDataSchema:
        """Resolve and normalize the nutrition response for *profile_id*."""
        logger.info("nutrition.evaluate")
        return self._calculator.evaluate(profile_id)


def get_nutrition_controller(
    calculator: NutritionCalculator = Depends(get_nutrition_calculator),  # noqa: B008
) -> NutritionController:
    """Per-request factory that wires the nutrition calculator into the controller."""
    return NutritionController(calculator)


router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])


@router.post(
    "/evaluate",
    response_model=NutritionResponseDataSchema,
    summary="Evaluate a nutrition profile",
    responses={
        200: {
            "description": "Structured nutrition response with exactly 3 tips.",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/NutritionResponseDataSchema"
                    }
                }
            },
        },
    },
)
def evaluate_nutrition(
    payload: NutritionEvaluateRequest,
    controller: NutritionController = Depends(get_nutrition_controller),  # noqa: B008
) -> NutritionResponseDataSchema:
    """Return the nutrition response for the supplied profile.

    The response carries an introductory clinical overview, exactly three
    ordered ``TipSchema`` cards, an optional ``PhysicianSchema``
    recommendation, and a list of follow-up chips. The payload is
    validated against :class:`NutritionResponseDataSchema`, which
    enforces the exact-3-tip cardinality before serialization.
    """
    return controller.evaluate(payload.profileId)


__all__ = ["NutritionController", "router"]
