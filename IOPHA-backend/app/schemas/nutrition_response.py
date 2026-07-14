from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.physician.physician_schema import PhysicianSchema
from app.schemas.tip import TipSchema

EXACT_TIP_COUNT = 3


class NutritionEvaluateRequest(BaseModel):
    """Inbound payload for the nutrition evaluation endpoint."""

    model_config = ConfigDict(extra="forbid")

    profileId: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Identifier of the patient nutrition profile to evaluate",
    )


class NutritionResponseDataSchema(BaseModel):
    """Compound nutrition output returned by the evaluation endpoint.

    Mirrors the ``NutritionResponse`` contract consumed by the booking UI
    (``IOPHA-frontend/src/components/NutritionResponse/NutritionResponse.tsx``):
    an introductory clinical overview, exactly three numbered dietary ``TipSchema``
    cards, an optional ``PhysicianSchema`` recommendation, and a list of
    actionabe follow-up chips.

    ``model_config = ConfigDict(extra="forbid")`` enforces a rigid contract
    so no unplanned field can cross the API boundary, matching the
    defensive validation posture of the other response schemas.
    """

    model_config = ConfigDict(extra="forbid")

    introText: str = Field(
        ...,
        max_length=2000,
        description="Introductory clinical overview for the nutrition response",
    )
    tips: List[TipSchema] = Field(
        ...,
        description="Exactly 3 behavioral dietary tips",
    )
    physician: Optional[PhysicianSchema] = Field(
        None,
        description="Optional physician recommendation",
    )
    followUpChips: List[str] = Field(
        ...,
        description="Actionable workflow chips",
    )

    @field_validator("tips")
    @classmethod
    def _validate_exact_tip_count(cls, value: List[TipSchema]) -> List[TipSchema]:
        """Enforce the cardinality contract: the response carries exactly 3 tips."""
        if len(value) != EXACT_TIP_COUNT:
            raise ValueError("Tips collection must contain exactly 3 entries")
        return value
