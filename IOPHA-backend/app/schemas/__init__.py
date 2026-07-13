from app.schemas.physician.physician_schema import PhysicianSchema
from app.schemas.provider.mappers import map_provider_to_physician
from app.schemas.provider.provider_record import ProviderRecord
from app.schemas.timeslot import TimeSlotSchema
from app.schemas.tip import TipSchema

__all__ = [
    "PhysicianSchema",
    "ProviderRecord",
    "TimeSlotSchema",
    "TipSchema",
    "map_provider_to_physician",
]
