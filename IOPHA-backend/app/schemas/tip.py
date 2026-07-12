from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TipSchema(BaseModel):
    """External booking tip / advice contract returned by the tips API.

    Mirrors the ``Tip`` interface consumed by the booking UI
    (``IOPHA-frontend/src/components/NutritionResponse/TipCard.tsx``): an
    ordered, numbered advice card carrying a headline (``title``) and an
    elaborated body (``description``). ``id`` is optional because a freshly
    generated (not-yet-persisted) tip may not carry a database reference token.

    ``model_config = ConfigDict(extra="forbid")`` enforces a rigid contract so
    no unplanned field can cross the API boundary, matching the defensive
    validation posture of :class:`PhysicianSchema` and :class:`TimeSlotSchema`.
    """

    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = Field(
        default=None,
        description="Unique database reference token",
        examples=["tip-001"],
    )
    number: int = Field(
        ...,
        ge=1,
        description="Ordered indexing digit for card stacking, e.g., 1",
        examples=[1],
    )
    title: str = Field(
        ...,
        min_length=1,
        description="Actionable summary headline for clinical advice",
        examples=["Hydrate Early"],
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Elaborated body text detailing behavioral guidance",
        examples=["Drink plenty of water throughout the day."],
    )
