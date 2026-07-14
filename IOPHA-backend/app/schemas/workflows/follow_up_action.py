from pydantic import BaseModel, ConfigDict, Field


class FollowUpActionSchema(BaseModel):
    """Frontend-aligned follow-up action chip contract for the search response."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(
        ...,
        max_length=200,
        description="Action chip display text rendered on the client",
    )
    actionType: str = Field(
        ...,
        max_length=100,
        description="Enumeration target routing directive for client funnel",
    )
    providerId: str = Field(
        ...,
        max_length=100,
        description="Target provider system key binding for action routing",
    )
