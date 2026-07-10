from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PhysicianSchema(BaseModel):
    """Frontend-aligned physician contract (normalized for the directory UI)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique provider system key")
    name: str = Field(..., description="Full display name including credentials")
    specialty: str = Field(..., description="Primary practice area designation")
    distance: str = Field(
        ..., description="Calculated localized display distance string"
    )
    rating: float = Field(..., description="Aggregated quality review score")
    reviewCount: int = Field(
        ..., description="Total summation of patient ratings submitted"
    )
    nextAvailable: str = Field(
        ..., description="Human-readable timeline mapping for upcoming slot"
    )
    imageUrl: Optional[str] = Field(
        None, description="Static target server path for graphic resource profile"
    )
    facility: Optional[str] = Field(
        None, description="Primary healthcare building assignment label"
    )
