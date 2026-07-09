from app.schemas.physician.physician_schema import PhysicianSchema
from app.schemas.provider.provider_record import ProviderRecord


def map_provider_to_physician(record: ProviderRecord) -> PhysicianSchema:
    """Map an internal relational record to the external physician DTO.

    Only client-safe, frontend-aligned fields are projected. The internal
    ``db_primary_key`` structural identifier is intentionally excluded so it
    never leaks past the API boundary.
    """
    return PhysicianSchema(
        id=record.id,
        name=record.name,
        specialty=record.specialty,
        distance=record.distance,
        rating=record.rating,
        reviewCount=record.reviewCount,
        nextAvailable=record.nextAvailable,
        imageUrl=record.imageUrl,
        facility=record.facility,
    )
