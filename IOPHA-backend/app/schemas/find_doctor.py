from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.provider.provider_schema import ProviderSchema
from app.schemas.workflows.follow_up_action import FollowUpActionSchema


class ProviderSearchRequest(BaseModel):
    """Inbound search payload for the provider discovery endpoint."""

    queryText: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language search query string",
    )


class FindDoctorResponseDataSchema(BaseModel):
    """Compound discovery output returned by the provider search endpoint."""

    model_config = ConfigDict(extra="forbid")

    summaryText: str = Field(
        ...,
        max_length=2000,
        description="Natural language system summary matching the search query result",
    )
    providers: list[ProviderSchema] = Field(
        ...,
        description="Collection of matching verified healthcare provider entities",
    )
    followUpActions: List[FollowUpActionSchema] = Field(
        ...,
        description="Action chips coordinating target client funnel redirects",
    )
