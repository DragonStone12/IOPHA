import logging
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_nutrition_calculator
from app.exceptions import NutritionEvaluationEngineError
from app.main import app
from app.schemas.nutrition_response import NutritionResponseDataSchema
from app.services.nutrition_service import NutritionCalculator

LEAK_MARKERS = (
    "Traceback",
    "Exception(",
    "0x",
    "password",
    "secret",
    "Bearer ",
    "postgresql",
)


class _CaptureHandler(logging.Handler):
    def __init__(self, sink: list[logging.LogRecord]) -> None:
        super().__init__()
        self._sink = sink

    def emit(self, record: logging.LogRecord) -> None:
        self._sink.append(record)


@pytest.fixture
def log_records() -> Generator[list[logging.LogRecord], None, None]:
    records: list[logging.LogRecord] = []
    handler = _CaptureHandler(records)
    logger = logging.getLogger("iopha.backend")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        yield records
    finally:
        logger.removeHandler(handler)


class MockNutritionCalculator(NutritionCalculator):
    """Fault-injectable test double for the nutrition calculator."""

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


def test_nutrition_evaluation_happy_path(
    log_records: list[logging.LogRecord],
) -> None:
    request_id = "11111111-1111-1111-1111-111111111111"
    with TestClient(app) as client:
        response = client.post(
            "/api/nutrition/evaluate",
            json={"profileId": "valid-profile"},
            headers={"X-Request-ID": request_id},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["introText"] == "Adjust micronutrient allocation."
    assert len(body["tips"]) == 3
    assert body["physician"]["name"] == "Dr. Emily Chen, MD"
    assert body["followUpChips"] == ["Book Specialist", "Export Plan"]

    record = next(
        (r for r in log_records if r.getMessage() == "nutrition.evaluate"),
        None,
    )
    assert record is not None
    assert record.getMessage() == "nutrition.evaluate"


def test_nutrition_evaluation_missing_profile_returns_422() -> None:
    with TestClient(app) as client:
        response = client.post("/api/nutrition/evaluate", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["status"] == 422
    assert body["title"] == "Unprocessable Content"
    assert body["instance"] == "/api/nutrition/evaluate"
    assert body["help_url"].endswith("#unprocessable-content-error")
    assert body["help_url"].startswith(
        "https://github.com/DragonStone12/IOPHA/blob/main/docs/RUNBOOKS.md#"
    )
    for marker in LEAK_MARKERS:
        assert marker not in response.text


def test_nutrition_evaluation_fault_injection(
    log_records: list[logging.LogRecord],
) -> None:
    request_id = "11111111-1111-1111-1111-111111111111"
    with TestClient(app) as client:
        response = client.post(
            "/api/nutrition/evaluate",
            json={"profileId": "corrupt-profile"},
            headers={"X-Request-ID": request_id},
        )
    assert response.status_code == 500
    body = response.json()
    assert body["status"] == 500
    assert body["title"] == "Nutritional Evaluation Processing Failure"
    assert body["instance"] == "/api/nutrition/evaluate"
    assert body["help_url"].endswith("#nutrition-evaluation-error")
    assert body["help_url"].startswith(
        "https://github.com/DragonStone12/IOPHA/blob/main/docs/RUNBOOKS.md#"
    )
    assert response.headers["X-Request-ID"] == request_id
    for marker in LEAK_MARKERS:
        assert marker not in response.text

    record = next(
        (
            r
            for r in log_records
            if r.getMessage() == "nutrition.evaluation_engine_error"
        ),
        None,
    )
    assert record is not None
    ctx = getattr(record, "extra_context", {})
    # The handler echoes the same correlation id the middleware
    # assigns and returns on X-Request-ID, so they must agree.
    assert ctx["requestId"] == response.headers["X-Request-ID"]
    assert ctx["path"] == "/api/nutrition/evaluate"
    assert ctx["profileId"] == "corrupt-profile"
