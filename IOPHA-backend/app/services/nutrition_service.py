from abc import ABC, abstractmethod

from app.schemas.nutrition_response import NutritionResponseDataSchema

_NUTRITION_SAMPLE: dict = {
    "introText": "Based on your goals, adjust micronutrient allocation.",
    "tips": [
        {"number": 1, "title": "Hydration", "description": "Drink 3L daily."},
        {"number": 2, "title": "Macros", "description": "Balance intake."},
        {"number": 3, "title": "Timing", "description": "Eat pre-workout."},
    ],
    "physician": {
        "id": "doc-88",
        "name": "Dr. Emily Chen, MD",
        "specialty": "Nutrition",
        "distance": "1.8 miles",
        "rating": 4.9,
        "reviewCount": 120,
        "nextAvailable": "Today",
    },
    "followUpChips": ["Book Specialist", "Export Plan"],
}


class NutritionCalculator(ABC):
    """Compute the structured nutrition response for a profile."""

    @abstractmethod
    def evaluate(self, profile_id: str) -> NutritionResponseDataSchema:
        """Return the nutrition response for *profile_id*."""


class InMemoryNutritionCalculator(NutritionCalculator):
    """No-backend stand-in that returns a deterministic sample payload."""

    def evaluate(self, profile_id: str) -> NutritionResponseDataSchema:
        return NutritionResponseDataSchema.model_validate(_NUTRITION_SAMPLE)
