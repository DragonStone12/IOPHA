from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_nutrition_calculator
from app.exceptions import NutritionEvaluationEngineError
from app.main import app
from app.schemas.nutrition_response import NutritionResponseDataSchema


class MockNutritionCalculator:
    """Fault-injectable stand-in for the nutrition calculator."""

    def evaluate(self, profile_id: str) -> NutritionResponseDataSchema:
        if profile_id == "corrupt-profile":
            raise NutritionEvaluationEngineError(profile_id)
        return NutritionResponseDataSchema.model_validate(
            {
                "introText": "Adjust micronutrient allocation.",
                "tips": [
                    {"number": 1, "title": "Hydration", "description": "Drink 3L."},
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
        )


@pytest.fixture(autouse=True)
def bind_nutrition_mock() -> Generator[None, None, None]:
    """Override the nutrition calculator dependency with the mock double."""
    app.dependency_overrides[get_nutrition_calculator] = lambda: (
        MockNutritionCalculator()
    )
    try:
        yield
    finally:
        # Pop only the key this fixture set; never clear() the whole
        # override map (see TROUBLESHOOTING.md: Python Testing Anti-Patterns).
        app.dependency_overrides.pop(get_nutrition_calculator, None)


def test_nutrition_evaluation_happy_path() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/nutrition/evaluate",
            json={"profileId": "valid-profile"},
        )
    assert response.status_code == 200
    body = response.json()
    assert len(body["tips"]) == 3
    assert body["physician"]["name"] == "Dr. Emily Chen, MD"
    assert body["followUpChips"] == ["Book Specialist", "Export Plan"]


def test_nutrition_evaluation_missing_profile_returns_422() -> None:
    with TestClient(app) as client:
        response = client.post("/api/nutrition/evaluate", json={})
    assert response.status_code == 422
    assert "help_url" in response.json()


def test_nutrition_evaluation_fault_injection() -> None:
    valid_request_id = "11111111-1111-1111-1111-111111111111"
    with TestClient(app) as client:
        response = client.post(
            "/api/nutrition/evaluate",
            json={"profileId": "corrupt-profile"},
            headers={"X-Request-ID": valid_request_id},
        )
    assert response.status_code == 500
    body = response.json()
    assert "help_url" in body
    assert "nutrition-evaluation-error" in body["help_url"]
    # The tracing middleware trusts only well-formed UUIDs; it echoes
    # the resolved correlation id back on the response header.
    assert response.headers["X-Request-ID"] == valid_request_id
